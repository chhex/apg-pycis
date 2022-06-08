from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit import PromptSession, prompt
class YesNoValidator(Validator): 
    def validate(self, document):
        text = document.text

        if text != "Y" and text != 'n':
            raise ValidationError(message='Please enter Y or n',cursor_position=1)


result = prompt(f"Continue with some func? ('Y' or 'n') :" ,validator=YesNoValidator())
print(result)