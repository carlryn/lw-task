# This script contains the code for building a Modal app that uses the Text Generation Inference (TGI) service to generate text based on a prompt.
# To run this script, you need to have a modal account configured on your local machine.
# In the modal dashboard you need to add a secret named my-huggingface-secret with the value of your Hugging Face API key.
# That is because Llama models on HuggingFace hub are gated.

import subprocess
from modal import App, Image, enter, exit, gpu
import modal


MODEL_DIR = "/model"
MODEL_ID = "meta-llama/Meta-Llama-3.1-8B-Instruct"

LAUNCH_FLAGS = [
    "--model-id",
    MODEL_ID,
    "--port",
    "8000",
    "--max-batch-prefill-tokens",
    "20000",
    "--max-total-tokens",
    "40000",
    "--max-input-tokens",
    "20000",
]


def download_model_to_image():
    subprocess.run(
        [
            "text-generation-server",
            "download-weights",
            MODEL_ID,
        ],
    )


app = App("example-tgi-" + MODEL_ID.split("/")[-1])
print(app.name)

tgi_image = (
    Image.from_registry("ghcr.io/huggingface/text-generation-inference:2.2")
    .dockerfile_commands("ENTRYPOINT []")
    .run_function(
        download_model_to_image,
        secrets=[modal.Secret.from_name("my-huggingface-secret")],
        timeout=3600,
        kwargs={"model_dir": MODEL_DIR, "model_name": MODEL_ID},
    )
    .pip_install("text-generation", "pydantic>=2.0")
)

GPU_CONFIG = gpu.H100(count=2)  # 2 H100s for faster inference!


@app.cls(
    gpu=GPU_CONFIG,
    allow_concurrent_inputs=10,
    container_idle_timeout=60 * 10,
    timeout=60 * 60,
    image=tgi_image,
    concurrency_limit=1,
    keep_warm=1,
    secrets=[modal.Secret.from_name("my-huggingface-secret")],
)
class Model:
    @enter()
    def start_server(self):
        import socket
        import time

        from text_generation import AsyncClient

        self.launcher = subprocess.Popen(
            ["text-generation-launcher"] + LAUNCH_FLAGS,
        )
        self.client = AsyncClient("http://127.0.0.1:8000", timeout=60)

        # Poll until webserver at 127.0.0.1:8000 accepts connections before running inputs.
        def webserver_ready():
            try:
                socket.create_connection(("127.0.0.1", 8000), timeout=1).close()
                return True
            except (socket.timeout, ConnectionRefusedError):
                # Check if launcher webserving process has exited.
                # If so, a connection can never be made.
                retcode = self.launcher.poll()
                if retcode is not None:
                    raise RuntimeError(f"launcher exited unexpectedly with code {retcode}")
                return False

        while not webserver_ready():
            time.sleep(1.0)
        print("Webserver ready!")

    @exit()
    def terminate_server(self):
        self.launcher.terminate()

    @modal.method()
    async def generate(self, prompt: str):
        # Specific template for Llama
        prompt_template = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
        <|eot_id|><|start_header_id|>user<|end_header_id|>

        {prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
        """
        result = await self.client.generate(
            prompt_template, max_new_tokens=4000, stop_sequences=["<|eot_id|>"]
        )
        return result.generated_text
