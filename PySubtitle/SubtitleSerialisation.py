import json

from PySubtitle.SubtitleLine import SubtitleLine
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleError import TranslationError
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleScene import SubtitleScene
from PySubtitle.Translation import Translation
from PySubtitle.TranslationPrompt import TranslationPrompt

# Serialisation helpers
def classname(obj):
    if isinstance(obj, type):
        return obj.__name__
    return type(obj).__name__

# Convert our custom types to JSON
class SubtitleEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, TranslationError):
            # Don't bother trying to serialise all the error types (why not?)
            return {
                "__class": classname(TranslationError),
                "type": classname(obj),
                "problem": str(obj)             
            }

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
                "sourcepath": obj.sourcepath,
                "outputpath": obj.outputpath,
                "scenecount": len(obj.scenes),
                "context": getattr(obj, 'context'),
                "scenes": obj.scenes,
            }
        elif isinstance(obj, SubtitleScene):
            return {
                "scene": getattr(obj, 'number'),
                "batchcount": obj.size,
                "linecount": obj.linecount,
                "all_translated": obj.all_translated,
                "context": {
                    "summary": obj.context.get('summary'),
                    "summaries": obj.context.get('summaries')
                },
                "batches": obj._batches,
            }
        elif isinstance(obj, SubtitleBatch):
            return {
                "scene": getattr(obj, 'scene'),
                "batch": getattr(obj, 'number'),
                "size": obj.size,
                "all_translated": obj.all_translated,
                "errors": obj.errors if obj.errors else None,
                "summary": getattr(obj, 'summary'),
                "originals": obj._originals,
                "translated": obj._translated,
                "context": {
                    "summary": obj.context.get('summary'),
                    "summaries": obj.context.get('summaries')
                },
                "translation": obj.translation
            }
        elif isinstance(obj, SubtitleLine):
            return {
                "line": obj.line,
                "translation": getattr(obj, 'translation'),
            }
        elif isinstance(obj, Translation):
            return {
                "text": obj._text,
                "summary": obj.summary,
                "synopsis": obj.synopsis,
                "characters": obj.characters,
                "prompt": obj.prompt,
                "finish_reason": obj.response.get('finish_reason') if obj.response else None,
                "response_time": obj.response.get('response_time') if obj.response else None,
                "prompt_tokens": obj.response.get('prompt_tokens') if obj.response else None,
                "completion_tokens": obj.response.get('completion_tokens') if obj.response else None,
                "total_tokens": obj.response.get('total_tokens') if obj.response else None
            }
        elif isinstance(obj, TranslationPrompt):
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
                obj = SubtitleFile(dct.get('outputpath') or dct.get('filename'))
                obj.sourcepath = dct.get('sourcepath') or obj.sourcepath
                obj.context = dct.get('context')
                obj.scenes = dct.get('scenes', [])
                return obj
            elif class_name == classname(SubtitleScene):
                obj = SubtitleScene(dct)
                return obj
            elif class_name == classname(SubtitleBatch):
                return SubtitleBatch(dct)
            elif class_name == classname(SubtitleLine) or class_name == "Subtitle": # TEMP backward compatibility
                return SubtitleLine(dct.get('line'), translation=dct.get('translation'))
            elif class_name == classname(Translation) or class_name == "ChatGPTTranslation":
                response = {
                    'text' : dct.get('text'),
                    'finish_reason' : dct.get('finish_reason'),
                    'response_time' : dct.get('response_time'),
                    'prompt_tokens' : dct.get('prompt_tokens'),
                    'completion_tokens' : dct.get('completion_tokens'),
                    'total_tokens' : dct.get('total_tokens'),
                    }
                
                if isinstance(response['text'], list):
                    # This shouldn't happen, but try to recover if it does
                    response['text'] = '\n'.join(response['text'])

                obj = Translation(response, dct.get('prompt'))
                obj.context = {
                    'summary': dct.get('summary', None),
                    'scene': dct.get('scene', None),
                    'synopsis': dct.get('synopsis', None),
                    'characters': dct.get('characters', None),
                }
                return obj
            elif class_name == classname(TranslationPrompt) or class_name == "ChatGPTPrompt" or class_name == "GPTPrompt":
                obj = TranslationPrompt(dct.get('instructions'))
                obj.user_prompt = dct.get('user_prompt')
                obj.messages = dct.get('messages')
                return obj
            elif class_name == classname(TranslationError):
                return TranslationError(dct.get('message'))
            
        return dct

