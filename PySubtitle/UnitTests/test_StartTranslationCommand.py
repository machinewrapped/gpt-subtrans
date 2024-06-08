from copy import deepcopy

from GUI.Command import Command
from PySubtitle.Helpers.TestCases import CreateTestDataModelBatched, SubtitleTestCase
from PySubtitle.Helpers.Tests import log_info, log_input_expected_result, log_test_name

from GUI.Commands.SaveProjectFile import SaveProjectFile
from GUI.Commands.TranslateSceneCommand import TranslateSceneCommand
from GUI.ProjectDataModel import ProjectDataModel
from GUI.Commands.StartTranslationCommand import StartTranslationCommand

from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.UnitTests.TestData.chinese_dinner import chinese_dinner_data

test_cases = [
    {
        "data" : chinese_dinner_data,
        "commands" : [
            {
                "command" : "StartTranslationCommand",
                "options" : {
                    "resume" : False,
                    "multithreaded" : False,
                    "autosave" : False,
                    "scenes" : {
                        1 : {}
                    }
                },
                "expected_commands_to_queue" : [ TranslateSceneCommand ],
                "expected_translations" : [ (1, None, None) ],
                "expected_translated_batches": [ (1,1) ],
                "expected_untranslated_batches": [ (2,1), (3,1), (4,1) ]
            },
            {
                "command" : "StartTranslationCommand",
                "options" : {
                    "resume" : False,
                    "autosave" : True,
                    "scenes" : {
                        2 : {}
                    }
                },
                "expected_commands_to_queue" : [ TranslateSceneCommand, SaveProjectFile ],
                "expected_translations" : [ (2, None, None) ],
                "expected_translated_batches": [ (1,1), (2,1) ],
                "expected_untranslated_batches": [ (3,1), (4,1) ]
            },
            {
                "command" : "StartTranslationCommand",
                "options" : {
                    "resume" : True,
                    "scenes" : {
                        1 : {},
                        2 : {}
                    }
                },
                "expected_commands_to_queue" : [],
                "expected_translations" : [],
                "expected_translated_batches": [ (1,1), (2,1) ],
                "expected_untranslated_batches": [ (3,1), (4,1) ]
            },
            {
                "command" : "StartTranslationCommand",
                "options" : {
                    "resume" : True,
                    "scenes" : {
                        1 : {},
                        2 : {},
                        3 : { 'batches': [1] }
                    }
                },
                "expected_commands_to_queue" : [ TranslateSceneCommand ],
                "expected_translations" : [ (3, [1], None) ],
                "expected_translated_batches": [ (1,1), (2,1), (3,1) ],
                "expected_untranslated_batches": [ (4,1) ]
            },
            {
                "command" : "StartTranslationCommand",
                "options" : {
                    "resume" : True,
                    "autosave" : True,
                },
                "expected_commands_to_queue" : [ TranslateSceneCommand, SaveProjectFile ],
                "expected_translations" : [ (4, None, None) ],
                "expected_translated_batches": [ (1,1), (2,1), (3,1), (4,1) ],
                "expected_untranslated_batches": []
            },
        ]
    }
]

class StartTranslationCommandTests(SubtitleTestCase):
    def __init__(self, methodName):
        super().__init__(methodName, custom_options={
            'max_batch_size': 100,
        })

    def test_StartTranslationCommand(self):
        log_test_name("StartTranslation tests")

        for case in test_cases:
            data = deepcopy(case.get('data'))
            log_test_name(f"Testing StartTranslation of {data.get('movie_name')}")

            datamodel : ProjectDataModel = CreateTestDataModelBatched(data, options=self.options, translated=False)
            subtitles : SubtitleFile = datamodel.project.subtitles

            commands = case.get('commands')

            for command_data in commands:
                command = self._create_command(command_data, datamodel)
                self.assertTrue(command.execute())

                queued_commands = self._flatten_queued_commands(command)
                queued_command_types = [type(command) for command in queued_commands]

                expected_commands_to_queue = command_data.get('expected_commands_to_queue')
                expected_translations = command_data.get('expected_translations')
                log_input_expected_result("Queued commands", queued_command_types, expected_commands_to_queue)

                self.assertEqual(len(queued_commands), len(expected_commands_to_queue))
                self.assertSequenceEqual(queued_command_types, expected_commands_to_queue)

                for command in queued_commands:
                    if isinstance(command, TranslateSceneCommand):
                        key = (command.scene_number, command.batch_numbers, command.line_numbers)
                        log_info(f"Validating translation of {key}")
                        self.assertIn(key, expected_translations)

                        self.assertTrue(command.execute())

                        self._validate_translated_batches(subtitles, command_data)
                        self._validate_untranslated_batches(subtitles, command_data)

    def _create_command(self, command_data, datamodel : ProjectDataModel):
        command_name = command_data.get('command')
        options = command_data.get('options')
        datamodel.UpdateProjectSettings({
            'autosave': options.get('autosave', False)
            })

        if command_name == "StartTranslationCommand":
            resume = options.get('resume', False)
            multithreaded = options.get('multithreaded', False)
            scenes = options.get('scenes', None)
            return StartTranslationCommand(datamodel=datamodel, resume=resume, multithreaded=multithreaded, scenes=scenes)

    def _flatten_queued_commands(self, command : Command):
        """
        Descend into the command tree and return a flat list of all commands to be executed
        """
        commands = []
        for queued_command in command.commands_to_queue:
            commands.append(queued_command)
            if command.commands_to_queue:
                commands.extend(self._flatten_queued_commands(queued_command))

        return commands

    def _validate_translated_batches(self, subtitles : SubtitleFile, command_data : dict):
        expected_translated_batches = command_data.get('expected_translated_batches', [])
        for scene_number, batch_number in expected_translated_batches:
            batch : SubtitleBatch = subtitles.GetBatch(scene_number, batch_number)
            self.assertIsNotNone(batch)
            self.assertTrue(batch.any_translated)

    def _validate_untranslated_batches(self, subtitles : SubtitleFile, command_data : dict):
        expected_untranslated_batches = command_data.get('expected_untranslated_batches', [])
        for scene_number, batch_number in expected_untranslated_batches:
            batch : SubtitleBatch = subtitles.GetBatch(scene_number, batch_number)
            self.assertIsNotNone(batch)
            self.assertFalse(batch.any_translated)
