# Copyright 2023 Intrinsic Innovation LLC

import io
import os

from absl.testing import absltest
from absl.testing import absltest
from intrinsic.solutions.internal import skill_providing
from intrinsic.solutions.internal import stubs
from intrinsic.solutions.internal import stubs_test_pb2
from intrinsic.solutions.testing import skill_test_utils


_INTRINSIC_STUBS_SOLUTIONS_PATH = (
    "intrinsic-stubs/solutions"
)
_INTRINSIC_STUBS_PATH = "intrinsic-stubs"


def _read_tmp_file(tmp_dir: absltest._TempDir, relative_path: str) -> str:
  with open(os.path.join(tmp_dir, relative_path), "r") as file:
    return file.read()


class StubsTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self._utils = skill_test_utils.SkillTestUtils(
        "internal/stubs_test_proto_descriptors_transitive_set_sci.proto.bin"
    )

  def assert_regex_with_pretty_printing(
      self, text: str, expected_regex: str
  ) -> None:
    self.assertRegex(
        text,
        expected_regex,
        "Content not maching regex (pretty printed):\n" + text,
    )

  def test_providers_stub(self):
    skill_infos = [
        self._utils.create_parameterless_skill_info("ai.intr.skill_one"),
        self._utils.create_parameterless_skill_info("ai.intr.skill_two"),
        self._utils.create_parameterless_skill_info("ai.ai_skill"),
        self._utils.create_parameterless_skill_info("foo.foo_skill"),
        self._utils.create_parameterless_skill_info("global_skill"),
    ]
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_infos(skill_infos),
        self._utils.create_empty_resource_registry(),
    )
    tmp_dir = self.create_tempdir()

    stubs.generate(tmp_dir.full_path, skills, io.StringIO())

    content = _read_tmp_file(
        tmp_dir, _INTRINSIC_STUBS_SOLUTIONS_PATH + "/providers.pyi"
    )

    # Smoke checks to see if the original content from providers.py is there and
    # if docstrings were preserved.
    self.assertIn("class ResourceProvider(abc.ABC):", content)
    self.assertIn("Provides access resources from a solution.", content)
    self.assertIn(
        "def __getattr__(self, name: str) -> provided.ResourceHandle:", content
    )
    self.assertIn("class SkillProvider(abc.ABC):", content)
    self.assertIn(
        "A container that provides access to the skills of a solution.", content
    )
    self.assertIn("def get_skill_ids(self) -> Iterable[str]:", content)

    # Test that imports were added.
    self.assert_regex_with_pretty_printing(
        content,
        r'(?s)^"""[^"]*"""\n.*'
        r"import intrinsic.solutions.skills\n.*"
        r"import intrinsic.solutions.skills.ai\n.*"
        r"import intrinsic.solutions.skills.ai.intr\n.*"
        r"import intrinsic.solutions.skills.foo\n+"
        "class ResourceProvider",
    )

    skill_provider_pos = content.find("class SkillProvider(abc.ABC):")
    skill_provider_content = content[skill_provider_pos:]

    # Test that some methods were removed from the SkillProvider class.
    self.assertNotIn("def __getattr__", skill_provider_content)
    self.assertNotIn("def __dir__", skill_provider_content)

    # Test that the skills are defined on the SkillProvider class.
    self.assert_regex_with_pretty_printing(
        skill_provider_content,
        r'''(?s)class SkillProvider\(abc.ABC\):
    """[^"]*"""\n*
    global_skill = intrinsic.solutions.skills.global_skill

    class ai:
        """.*Namespace class for the skill package 'ai'[^"]*"""\n*
        ai_skill = intrinsic.solutions.skills.ai.ai_skill\n*

        class intr:
            """.*Namespace class for the skill package 'ai.intr'[^"]*"""\n*
            skill_one = intrinsic.solutions.skills.ai.intr.skill_one
            skill_two = intrinsic.solutions.skills.ai.intr.skill_two\n*

    class foo:
        """.*Namespace class for the skill package 'foo'[^"]*"""\n*
        foo_skill = intrinsic.solutions.skills.foo.foo_skill''',
    )

  def test_py_typed(self):
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_infos([]),
        self._utils.create_empty_resource_registry(),
    )
    tmp_dir = self.create_tempdir()

    stubs.generate(tmp_dir.full_path, skills, io.StringIO())

    content = _read_tmp_file(tmp_dir, _INTRINSIC_STUBS_PATH + "/py.typed")

    self.assertEqual("partial\n", content)

  def test_generates_one_skill_module_stub_for_each_skill_package(self):
    skill_infos = [
        self._utils.create_parameterless_skill_info("ai.intr.skill_one"),
        self._utils.create_parameterless_skill_info("ai.intr.skill_two"),
        self._utils.create_parameterless_skill_info("ai.ai_skill"),
        self._utils.create_parameterless_skill_info("foo.foo_skill"),
        self._utils.create_parameterless_skill_info("global_skill"),
    ]
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_infos(skill_infos),
        self._utils.create_empty_resource_registry(),
    )
    tmp_dir = self.create_tempdir()

    stubs.generate(tmp_dir.full_path, skills, io.StringIO())

    for relative_path in [
        "skills/ai/intr/__init__.pyi",
        "skills/ai/__init__.pyi",
        "skills/foo/__init__.pyi",
        "skills/__init__.pyi",
    ]:
      path = os.path.join(
          tmp_dir, _INTRINSIC_STUBS_SOLUTIONS_PATH, relative_path
      )
      self.assertTrue(os.path.isfile(path), f"{path} does not exist")

  def test_skill_module_stub_for_paramless_skills(self):
    skill_infos = [
        self._utils.create_parameterless_skill_info("ai.intr.skill_one"),
        self._utils.create_parameterless_skill_info("ai.intr.skill_two"),
    ]
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_infos(skill_infos),
        self._utils.create_empty_resource_registry(),
    )
    tmp_dir = self.create_tempdir()

    stubs.generate(tmp_dir.full_path, skills, io.StringIO())

    content = _read_tmp_file(
        tmp_dir,
        _INTRINSIC_STUBS_SOLUTIONS_PATH + "/skills/ai/intr/__init__.pyi",
    )

    self.assert_regex_with_pretty_printing(
        content,
        r'''"""Skill classes for the skills in the skill package 'ai.intr'.
[^"]*skill_one[^"]*skill_two[^"]*"""\n*
from __future__ import annotations
from intrinsic.solutions.internal import skill_generation\n*

class skill_one\(skill_generation.GeneratedSkill\):
    """Skill class[^"]*ai.intr.skill_one[^"]*"""\n*

    def __init__\(self\):
        """Initializes[^"]*ai.intr.skill_one[^"]*"""
        \.\.\.\n*

class skill_two\(skill_generation.GeneratedSkill\):
    """Skill class[^"]*ai.intr.skill_two[^"]*"""\n*

    def __init__\(self\):
        """Initializes[^"]*ai.intr.skill_two[^"]*"""
        \.\.\.''',
    )

  def test_skill_init_signature_with_basic_params(self):
    skill_info = self._utils.create_test_skill_info_with_return_value(
        "ai.intr.my_skill",
        parameter_defaults=stubs_test_pb2.BasicParams(),
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )
    tmp_dir = self.create_tempdir()

    stubs.generate(tmp_dir.full_path, skills, io.StringIO())

    content = _read_tmp_file(
        tmp_dir,
        _INTRINSIC_STUBS_SOLUTIONS_PATH + "/skills/ai/intr/__init__.pyi",
    )

    self.assertRegex(
        content, r'"""[^"]*"""\n*from __future__ import annotations\n'
    )
    self.assertIn("from collections.abc import Sequence\n", content)
    self.assertIn(
        "from intrinsic.solutions.internal import skill_generation\n",
        content,
    )
    self.assertIn(
        "from intrinsic.solutions.provided import ParamAssignment\n",
        content,
    )

    self.assert_regex_with_pretty_printing(
        content,
        r"class my_skill\(skill_generation.GeneratedSkill\):\n*"
        r'    """[^"]*my_skill[^"]*"""\n*'
        r"    def __init__\(\s*"
        r"self,\s*"
        r"\*,\s*"
        r"required_double: float \| ParamAssignment,\s*"
        r"required_message:"
        r" \(?\s*my_skill.intrinsic_proto.stubs_test.EmptyMessage\s*\|"
        r" ParamAssignment\s*\)?,\s*"
        r"my_enum:"
        r" \(?\s*my_skill.intrinsic_proto.stubs_test.BasicParams.MyEnum\s*\|"
        r" ParamAssignment\s*\)?,\s*"
        r"my_double: float \| ParamAssignment \| None = ...,\s*"
        r"my_int: int \| ParamAssignment \| None = ...,\s*"
        r"my_bool: bool \| ParamAssignment \| None = ...,\s*"
        r"my_string: str \| ParamAssignment \| None = ...,\s*"
        r"repeated_double: \(?\s*Sequence\[float \| ParamAssignment] \|"
        r" ParamAssignment\s*\)? = \[\],\s*"
        r"optional_message:"
        r" \(?\s*my_skill.intrinsic_proto.stubs_test.EmptyMessage\s*\|"
        r" ParamAssignment\s*\| None\s*\)? = ...,\s*"
        r"repeated_message:"
        r" \(?\s*Sequence\[\s*my_skill.intrinsic_proto.stubs_test.EmptyMessage\s*\|"
        r" ParamAssignment\s*\]\s*\| ParamAssignment\s*\)? = \[\],\s*"
        r"string_int_map: dict\[str, int\] \| ParamAssignment = \{\},\s*"
        r"string_message_map: \(?\s*dict\[str,"
        r" my_skill.intrinsic_proto.stubs_test.EmptyMessage\]\s*\|"
        r" ParamAssignment\s*\)? = \{\},\s*"
        r"return_value_key: str \| None = ...,?\s*"
        r"\):\s*"
        r'"""[^"]*Initializes[^"]*skill ai.intr.my_skill[^"]*"""\s*'
        r"\.\.\.",
    )

  def test_skill_init_signature_with_auto_conversion_params(self):
    skill_info = self._utils.create_test_skill_info(
        "ai.intr.my_skill",
        parameter_defaults=stubs_test_pb2.AutoConversionParams(),
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )
    tmp_dir = self.create_tempdir()

    stubs.generate(tmp_dir.full_path, skills, io.StringIO())

    content = _read_tmp_file(
        tmp_dir,
        _INTRINSIC_STUBS_SOLUTIONS_PATH + "/skills/ai/intr/__init__.pyi",
    )

    self.assertRegex(
        content, r'"""[^"]*"""\n*from __future__ import annotations\n'
    )
    self.assertIn("import datetime\n", content)
    self.assertIn("from intrinsic.math.python import data_types\n", content)
    self.assertIn(
        "from intrinsic.solutions.internal import skill_generation\n",
        content,
    )
    self.assertIn(
        "from intrinsic.solutions.provided import ParamAssignment\n",
        content,
    )
    self.assertIn(
        "from intrinsic.world.python import object_world_resources\n",
        content,
    )

    self.assert_regex_with_pretty_printing(
        content,
        r"class my_skill\(skill_generation.GeneratedSkill\):\n*"
        r'    """[^"]*my_skill[^"]*"""\n*'
        r"    def __init__\(\s*"
        r"self,\s*"
        r"\*,\s*"
        r"duration: \(\s*datetime.timedelta\s*\| float\s*\| int\s*\|"
        r" my_skill.google.protobuf.Duration\s*\| ParamAssignment\s*\),\s*"
        r"pose: data_types.Pose3 \| my_skill.intrinsic_proto.Pose \|"
        r" ParamAssignment,\s*"
        r"object_reference: \(\s*object_world_resources.TransformNode\s*\|"
        r" my_skill.intrinsic_proto.world.ObjectReference\s*\|"
        r" ParamAssignment\s*\),\s*"
        r"\):\s*"
        r'"""[^"]*Initializes[^"]*skill ai.intr.my_skill[^"]*"""\s*'
        r"\.\.\.",
    )

  def test_enum_defs(self):
    skill_info = self._utils.create_test_skill_info(
        "ai.intr.my_skill",
        parameter_defaults=stubs_test_pb2.ParamsWithVariousEnums(),
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )
    tmp_dir = self.create_tempdir()

    stubs.generate(tmp_dir.full_path, skills, io.StringIO())

    content = _read_tmp_file(
        tmp_dir,
        _INTRINSIC_STUBS_SOLUTIONS_PATH + "/skills/ai/intr/__init__.pyi",
    )

    self.assert_regex_with_pretty_printing(
        content,
        r'''(?s)\
class my_skill\(skill_generation.GeneratedSkill\):.*
    LOCAL_ENUM_FIRST_VALUE = \(?\s*my_skill.intrinsic_proto.stubs_test.ParamsWithVariousEnums.ParamsEnum.LOCAL_ENUM_FIRST_VALUE\s*\)?
    LOCAL_ENUM_SECOND_VALUE = \(?\s*my_skill.intrinsic_proto.stubs_test.ParamsWithVariousEnums.ParamsEnum.LOCAL_ENUM_SECOND_VALUE\s*\)?
    LOCAL_ENUM_UNSPECIFIED = \(?\s*my_skill.intrinsic_proto.stubs_test.ParamsWithVariousEnums.ParamsEnum.LOCAL_ENUM_UNSPECIFIED\s*\)?.*

    class intrinsic_proto:.*
        class stubs_test:.*
            GLOBAL_ENUM_FIRST_VALUE = \(?\s*my_skill.intrinsic_proto.stubs_test.GlobalEnum.GLOBAL_ENUM_FIRST_VALUE\s*\)?
            GLOBAL_ENUM_SECOND_VALUE = \(?\s*my_skill.intrinsic_proto.stubs_test.GlobalEnum.GLOBAL_ENUM_SECOND_VALUE\s*\)?
            GLOBAL_ENUM_UNSPECIFIED = \(?\s*my_skill.intrinsic_proto.stubs_test.GlobalEnum.GLOBAL_ENUM_UNSPECIFIED\s*\)?

            class GlobalEnum\(enum.IntEnum\):
                GLOBAL_ENUM_UNSPECIFIED = 0
                GLOBAL_ENUM_FIRST_VALUE = 1
                GLOBAL_ENUM_SECOND_VALUE = 2.*

            class ParamsWithVariousEnums:.*
                LOCAL_ENUM_FIRST_VALUE = \(?\s*my_skill.intrinsic_proto.stubs_test.ParamsWithVariousEnums.ParamsEnum.LOCAL_ENUM_FIRST_VALUE\s*\)?
                LOCAL_ENUM_SECOND_VALUE = \(?\s*my_skill.intrinsic_proto.stubs_test.ParamsWithVariousEnums.ParamsEnum.LOCAL_ENUM_SECOND_VALUE\s*\)?
                LOCAL_ENUM_UNSPECIFIED = \(?\s*my_skill.intrinsic_proto.stubs_test.ParamsWithVariousEnums.ParamsEnum.LOCAL_ENUM_UNSPECIFIED\s*\)?

                class ParamsEnum\(enum.IntEnum\):
                    LOCAL_ENUM_UNSPECIFIED = 0
                    LOCAL_ENUM_FIRST_VALUE = 1
                    LOCAL_ENUM_SECOND_VALUE = 2.*

            class UnusedMessage:
                """[^"]*Namespace class[^"]*""".*
                USED_ENUM_FIRST_VALUE = \(?\s*my_skill.intrinsic_proto.stubs_test.UnusedMessage.UsedEnum.USED_ENUM_FIRST_VALUE\s*\)?
                USED_ENUM_SECOND_VALUE = \(?\s*my_skill.intrinsic_proto.stubs_test.UnusedMessage.UsedEnum.USED_ENUM_SECOND_VALUE\s*\)?
                USED_ENUM_UNSPECIFIED = \(?\s*my_skill.intrinsic_proto.stubs_test.UnusedMessage.UsedEnum.USED_ENUM_UNSPECIFIED\s*\)?

                class UsedEnum\(enum.IntEnum\):
                    USED_ENUM_UNSPECIFIED = 0
                    USED_ENUM_FIRST_VALUE = 1
                    USED_ENUM_SECOND_VALUE = 2''',
    )

  def test_multiple_wrapper_class_defs_for_single_skill(self):
    skill_info = self._utils.create_test_skill_info(
        "ai.intr.my_skill",
        parameter_defaults=stubs_test_pb2.VariousMessageParams(),
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )
    tmp_dir = self.create_tempdir()

    stubs.generate(tmp_dir.full_path, skills, io.StringIO())

    content = _read_tmp_file(
        tmp_dir,
        _INTRINSIC_STUBS_SOLUTIONS_PATH + "/skills/ai/intr/__init__.pyi",
    )

    self.assert_regex_with_pretty_printing(
        content,
        r'''(?s)
class my_skill\(skill_generation.GeneratedSkill\):.*
        \.\.\.\s*

    class intrinsic_proto:\n*
        """[^"]*Namespace class[^"]*intrinsic_proto[^"]*"""\n*

        class Point:\n*
            """[^"]*wrapper class[^"]*intrinsic_proto.Point[^"]*""".*

        class Pose:\n*
            """[^"]*wrapper class[^"]*intrinsic_proto.Pose[^"]*""".*

        class Quaternion:\n*
            """[^"]*wrapper class[^"]*intrinsic_proto.Quaternion[^"]*""".*

        class stubs_test:\n*
            """[^"]*Namespace class[^"]*intrinsic_proto.stubs_test[^"]*"""\n*

            class AnotherOuterMessage:\n*
                """[^"]*wrapper class[^"]*intrinsic_proto.stubs_test.AnotherOuterMessage[^"]*""".*

                class AnotherNestedMessage:\n*
                    """[^"]*wrapper class[^"]*intrinsic_proto.stubs_test.AnotherOuterMessage.AnotherNestedMessage[^"]*""".*

            class EmptyMessage:\n*
                """[^"]*wrapper class[^"]*intrinsic_proto.stubs_test.EmptyMessage[^"]*""".*

            class OuterMessage:\n*
                """[^"]*Namespace class[^"]*intrinsic_proto.stubs_test.OuterMessage[^"]*"""\n*

                class NestedMessage:\n*
                    """[^"]*wrapper class[^"]*intrinsic_proto.stubs_test.OuterMessage.NestedMessage[^"]*"""
''',
    )

  def test_wrapper_init_signature(self):
    skill_info = self._utils.create_test_skill_info(
        "ai.intr.my_skill",
        parameter_defaults=stubs_test_pb2.NestedBasicParams(),
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )
    tmp_dir = self.create_tempdir()

    stubs.generate(tmp_dir.full_path, skills, io.StringIO())

    content = _read_tmp_file(
        tmp_dir,
        _INTRINSIC_STUBS_SOLUTIONS_PATH + "/skills/ai/intr/__init__.pyi",
    )

    self.assertRegex(
        content, r'"""[^"]*"""\n*from __future__ import annotations\n'
    )
    self.assertIn("from collections.abc import Sequence\n", content)
    self.assertIn(
        "from intrinsic.solutions.internal import skill_generation\n",
        content,
    )
    self.assertIn(
        "from intrinsic.solutions.provided import ParamAssignment\n",
        content,
    )

    self.assert_regex_with_pretty_printing(
        content,
        r'''(?s)
class my_skill\(skill_generation.GeneratedSkill\):.*
    class intrinsic_proto:.*
        class stubs_test:.*
            class BasicParams:
                """[^"]*"""\n*
                def __init__\(\s*'''
        r"self,\s*"
        r"\*,\s*"
        r"required_double: float \| ParamAssignment,\s*"
        r"required_message:"
        r" \(?\s*my_skill.intrinsic_proto.stubs_test.EmptyMessage\s*\|"
        r" ParamAssignment\s*\)?,\s*"
        r"my_enum:"
        r" \(?\s*my_skill.intrinsic_proto.stubs_test.BasicParams.MyEnum\s*\|"
        r" ParamAssignment\s*\)?,\s*"
        r"my_double: float \| ParamAssignment \| None = ...,\s*"
        r"my_int: int \| ParamAssignment \| None = ...,\s*"
        r"my_bool: bool \| ParamAssignment \| None = ...,\s*"
        r"my_string: str \| ParamAssignment \| None = ...,\s*"
        r"repeated_double: \(?\s*Sequence\[float \| ParamAssignment] \|"
        r" ParamAssignment\s*\)? = \[\],\s*"
        r"optional_message:"
        r" \(?\s*my_skill.intrinsic_proto.stubs_test.EmptyMessage\s*\|"
        r" ParamAssignment\s*\| None\s*\)? = ...,\s*"
        r"repeated_message:"
        r" \(?\s*Sequence\[\s*my_skill.intrinsic_proto.stubs_test.EmptyMessage\s*\|"
        r" ParamAssignment\s*\]\s*\| ParamAssignment\s*\)? = \[\],\s*"
        r"string_int_map: dict\[str, int\] \| ParamAssignment = \{\},\s*"
        r"string_message_map: \(?\s*dict\[str,"
        r" my_skill.intrinsic_proto.stubs_test.EmptyMessage\]\s*\|"
        r" ParamAssignment\s*\)? = \{\},?\s*"
        r"\):\s*"
        r'"""[^"]*Initializes[^"]*intrinsic_proto.stubs_test.BasicParams[^"]*"""\s*'
        r"\.\.\.",
    )

  def test_output_gets_auto_formatted(self):
    skill_info = self._utils.create_test_skill_info(
        "ai.intr.my_skill",
        parameter_defaults=stubs_test_pb2.NestedBasicParams(),
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )
    tmp_dir = self.create_tempdir()

    stubs.generate(tmp_dir.full_path, skills, io.StringIO())

    for relative_path in [
        "/providers.pyi",
        "/skills/ai/intr/__init__.pyi",
    ]:
      content = _read_tmp_file(
          tmp_dir,
          _INTRINSIC_STUBS_SOLUTIONS_PATH + relative_path,
      )

      # Check the longest line length against the formatting column limit. Admit
      # some extra space for lines that cannot be squeezed into the column limit
      # (e.g. docstrings). Without auto-formatting the output would contain
      # **really** long lines because of unbroken function signatures.
      max_line_length = max(len(line) for line in content.split("\n"))
      self.assertLessEqual(
          max_line_length,
          stubs._FORMATTING_COLUMN_LIMIT + 20,
          f"Content exceeding max line length of {max_line_length}:\n{content}",
      )

  def test_prints_success_message(self):
    skill_info = self._utils.create_test_skill_info(
        "ai.intr.my_skill",
        parameter_defaults=stubs_test_pb2.EmptyMessage(),
    )
    skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(skill_info),
        self._utils.create_empty_resource_registry(),
    )
    other_skill_info = self._utils.create_test_skill_info(
        "ai.intr.my_skill",
        parameter_defaults=stubs_test_pb2.BasicParams(),
    )
    other_skills = skill_providing.Skills(
        self._utils.create_skill_registry_for_skill_info(other_skill_info),
        self._utils.create_empty_resource_registry(),
    )
    tmp_dir = self.create_tempdir()

    # Smoke test a few scenarios, this is not meant to be an exhaustive test.
    # Generate stubs for the first time.
    out = io.StringIO()
    stubs.generate(tmp_dir.full_path, skills, out)

    self.assertIn("successfully updated", out.getvalue())
    self.assertNotIn("VS Code", out.getvalue())

    # Generate same stubs again.
    out = io.StringIO()
    stubs.generate(tmp_dir.full_path, skills, out)

    self.assertIn("already up-to-date", out.getvalue())

    # Generate different stubs for different skills in a VS Code-like
    # environment.
    os.environ["VSCODE_CWD"] = "/some/path"

    out = io.StringIO()
    stubs.generate(tmp_dir.full_path, other_skills, out)

    self.assertIn("successfully updated", out.getvalue())
    self.assertIn("VS Code", out.getvalue())


if __name__ == "__main__":
  absltest.main()
