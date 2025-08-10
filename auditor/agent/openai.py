class DummyResponse:
    def __init__(self, output_text=""):
        self.output_text = output_text
        self.output = []

def openai_generate_response(*, messages, model, reasoning_effort):
    raise RuntimeError("OpenAI integration not available")

