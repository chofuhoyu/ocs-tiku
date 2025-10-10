from transformers import AutoModelForCausalLM, AutoTokenizer
from modelscope import snapshot_download


class Qwen3ModelService:

    def __init__(self, model_dir: str = "Qwen/Qwen3-8B"):
        model_dir = snapshot_download(model_dir)
        print(f'model dir is {model_dir}')

        # load the tokenizer and the model
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            dtype="auto",
            device_map="auto"
        )

    def generate(self, messages: list, max_new_tokens: int = 32768, enable_thinking: bool = True) -> tuple[str, str]:
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            # Switches between thinking and non-thinking modes. Default is True.
            enable_thinking=enable_thinking
        )
        model_inputs = self.tokenizer(
            [text], return_tensors="pt").to(self.model.device)

        # conduct text completion
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=max_new_tokens,
        )
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()

        # parsing thinking content
        try:
            # rindex finding 151668 (</think>)
            index = len(output_ids) - output_ids[::-1].index(151668)
        except ValueError:
            index = 0

        thinking_content = self.tokenizer.decode(
            output_ids[:index], skip_special_tokens=True).strip("\n")
        content = self.tokenizer.decode(
            output_ids[index:], skip_special_tokens=True).strip("\n")

        return thinking_content, content
