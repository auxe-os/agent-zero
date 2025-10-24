import json
import os

from agent import AgentContext, UserMessage
from flask import Response
from httpx import RemoteProtocolError
from werkzeug.utils import secure_filename

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response as ApiResponse
from python.helpers.defer import DeferredTask
from python.helpers.print_style import PrintStyle


class Message(ApiHandler):
    @classmethod
    def requires_csrf(cls) -> bool:
        return False  # Disable CSRF protection for message endpoint
    
    async def process(self, input: dict, request: Request) -> dict | ApiResponse:
        task, context = await self.communicate(input=input, request=request)
        return await self.respond(task, context)

    async def respond(self, task: DeferredTask, context: AgentContext):
        try:
            result = await task.result()  # type: ignore
        except RemoteProtocolError as error:
            error_message = (
                "The upstream model closed the connection before completing its response. "
                "Please try nudging the agent or resending your message."
            )
            PrintStyle().error(
                f"RemoteProtocolError while awaiting model response: {error}"
            )
            context.log.log(
                type="error",
                heading="Upstream connection error",
                content=error_message,
                kvps={"detail": str(error)},
            )
            payload = {
                "error": error_message,
                "context": context.id,
                "error_type": "RemoteProtocolError",
            }
            return Response(
                response=json.dumps(payload),
                status=502,
                mimetype="application/json",
            )
        return {
            "message": result,
            "context": context.id,
        }

    async def communicate(self, input: dict, request: Request):
        # Handle both JSON and multipart/form-data
        if request.content_type.startswith("multipart/form-data"):
            text = request.form.get("text", "")
            ctxid = request.form.get("context", "")
            message_id = request.form.get("message_id", None)
            attachments = request.files.getlist("attachments")
            attachment_paths = []

            upload_folder_int = "/a0/tmp/uploads"
            upload_folder_ext = files.get_abs_path("tmp/uploads") # for development environment

            if attachments:
                os.makedirs(upload_folder_ext, exist_ok=True)
                for attachment in attachments:
                    if attachment.filename is None:
                        continue
                    filename = secure_filename(attachment.filename)
                    save_path = files.get_abs_path(upload_folder_ext, filename)
                    attachment.save(save_path)
                    attachment_paths.append(os.path.join(upload_folder_int, filename))
        else:
            # Handle JSON request as before
            input_data = request.get_json()
            text = input_data.get("text", "")
            ctxid = input_data.get("context", "")
            message_id = input_data.get("message_id", None)
            attachment_paths = []

        # Now process the message
        message = text

        # Obtain agent context
        context = self.get_context(ctxid)

        # Store attachments in agent data
        # context.agent0.set_data("attachments", attachment_paths)

        # Prepare attachment filenames for logging
        attachment_filenames = (
            [os.path.basename(path) for path in attachment_paths]
            if attachment_paths
            else []
        )

        # Print to console and log
        PrintStyle(
            background_color="#6C3483", font_color="white", bold=True, padding=True
        ).print(f"User message:")
        PrintStyle(font_color="white", padding=False).print(f"> {message}")
        if attachment_filenames:
            PrintStyle(font_color="white", padding=False).print("Attachments:")
            for filename in attachment_filenames:
                PrintStyle(font_color="white", padding=False).print(f"- {filename}")

        # Log the message with message_id and attachments
        context.log.log(
            type="user",
            heading="User message",
            content=message,
            kvps={"attachments": attachment_filenames},
            id=message_id,
        )

        return context.communicate(UserMessage(message, attachment_paths)), context
