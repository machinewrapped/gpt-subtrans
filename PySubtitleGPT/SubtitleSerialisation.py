import json

from PySubtitleGPT.ChatGPTPrompt import ChatGPTPrompt
from PySubtitleGPT.Subtitle import Subtitle
from PySubtitleGPT.SubtitleBatch import SubtitleBatch
from PySubtitleGPT.SubtitleFile import SubtitleFile
from PySubtitleGPT.SubtitleScene import SubtitleScene
from PySubtitleGPT.ChatGPTTranslation import ChatGPTTranslation

# Serialisation helpers
def classname(obj):
    if isinstance(obj, type):
        return obj.__name__
    return type(obj).__name__

# Convert our custom types to JSON
class SubtitleEncoder(json.JSONEncoder):
    def default(self, obj):
        _class = classname(obj)
        properties = self.serialize_object(obj)
        if isinstance(properties, dict):
            properties = {k: v for k, v in properties.items() if v is not None}
            return {**{ "_class": _class }, **properties}
        else:
            return properties

    def serialize_object(self, obj):
        if obj is None:
            return None
        
        if isinstance(obj, SubtitleFile):
            return {
                "filename": obj.filename,
                "scenecount": len(obj.scenes),
                "context": getattr(obj, 'context'),
                "scenes": obj.scenes,
            }
        elif isinstance(obj, SubtitleScene):
            return {
                "number": getattr(obj, 'number'),
                "batchcount": obj.size,
                "linecount": obj.linecount,
                "all_translated": obj.all_translated,
                "context": {
                    "summary": obj.context.get('summary')
                },
                "batches": obj._batches,
            }
        elif isinstance(obj, SubtitleBatch):
            return {
                "number": getattr(obj, 'number'),
                "size": obj.size,
                "all_translated": obj.all_translated,
                "summary": getattr(obj, 'summary'),
                "subtitles": obj._subtitles,
                "translated": obj._translated,
                "context": {
                    "summary": obj.context.get('summary')
                },
                "translation": obj.translation
            }
        elif isinstance(obj, Subtitle):
            return {
                "line": obj.line,
                "translation": getattr(obj, 'translation'),
            }
        elif isinstance(obj, ChatGPTTranslation):
            return {
                "finish_reason": obj.finish_reason,
                "response_time": getattr(obj, 'response_time'),
                'prompt_tokens': getattr(obj, 'prompt_tokens'),
                'completion_tokens': getattr(obj, 'completion_tokens'),
                'total_tokens': getattr(obj, 'total_tokens'),
                "text": obj._text,
                "summary": obj.summary,
                "synopsis": obj.synopsis,
                "characters": obj.characters,
                "prompt": obj.prompt,
            }
        elif isinstance(obj, ChatGPTPrompt):
            return {
                "instructions": obj.instructions,
                "messages": obj.messages
            }
        return super().default(obj)

# Reconstruct our custom types from JSON
class SubtitleDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        if '_class' in dct:
            class_name = dct.pop('_class')
            if class_name == classname(SubtitleFile):
                obj = SubtitleFile(dct.get('filename'))
                obj.context = dct.get('context')
                obj.scenes = dct.get('scenes', [])
                return obj
            elif class_name == classname(SubtitleScene):
                obj = SubtitleScene()
                obj.number = dct.get('number')
                obj.context = dct.get('context')
                obj._batches = dct.get('batches')
                obj._summary = dct.get('summary')
                return obj
            elif class_name == classname(SubtitleBatch):
                return SubtitleBatch(dct)
            elif class_name == classname(Subtitle):
                return Subtitle(dct['line'], dct.get('translation'))
            elif class_name == classname(ChatGPTTranslation):
                response = {
                    'text' : dct.get('text'),
                    'finish_reason' : dct.get('finish_reason'),
                    'response_time' : dct.get('response_time'),
                    'prompt_tokens' : dct.get('prompt_tokens'),
                    'completion_tokens' : dct.get('completion_tokens'),
                    'total_tokens' : dct.get('total_tokens'),
                    }
                obj = ChatGPTTranslation(response, dct.get('prompt'))
                obj.summary = dct.get('summary', None)
                obj.synopsis = dct.get('synopsis', None)
                obj.characters = dct.get('characters', None)
                return obj
            elif class_name == classname(ChatGPTPrompt):
                obj = ChatGPTPrompt(dct.get('instructions'))
                obj.user_prompt = dct.get('user_prompt')
                obj.messages = dct.get('messages')
                return obj
        return dct

