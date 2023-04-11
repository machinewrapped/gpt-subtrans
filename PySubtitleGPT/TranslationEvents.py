from events import Events

class TranslationEvents(Events):
    __events__ = ( "preprocessed", "batch_translated", "scene_translated", "translation_complete" )

