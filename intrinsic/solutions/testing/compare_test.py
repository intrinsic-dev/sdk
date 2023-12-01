# Copyright 2023 Intrinsic Innovation LLC

"""Tests for intrinsic.solutions.testing.compare."""

import copy
# pylint:disable-next=g-importing-member
from intrinsic.executive.proto.test_message_pb2 import TestMessage
from intrinsic.solutions.testing import compare
from absl.testing import absltest
from absl.testing import parameterized

# match something like '?        ^^^^^^' with unknown position and size of the ^
mismatch_line_re = "\\? *[ -\\^]+"
non_mismatch_lines = "[^?]*"


class RemoveFieldTest(parameterized.TestCase):
  """Tests the _clear_field function."""

  @parameterized.named_parameters(
      dict(
          testcase_name="basic",
          msg_before=TestMessage(int64_value=42, string_value="protected"),
          field_path="int64_value",
          msg_after=TestMessage(string_value="protected"),
      ),
      dict(
          testcase_name="nested_field",
          msg_before=TestMessage(
              int64_value=77,
              message_value=TestMessage(
                  int64_value=42, string_value="protected"
              ),
              string_value="protected2",
          ),
          field_path="message_value.int64_value",
          msg_after=TestMessage(
              int64_value=77,
              message_value=TestMessage(string_value="protected"),
              string_value="protected2",
          ),
      ),
      dict(
          testcase_name="map",
          msg_before=TestMessage(
              string_int32_map={"foo": 42, "bar": 99}, string_value="protected"
          ),
          field_path="string_int32_map",
          msg_after=TestMessage(string_value="protected"),
      ),
      dict(
          testcase_name="repeated_field",
          msg_before=TestMessage(
              message_list=[
                  TestMessage(int64_value=42),
                  TestMessage(int64_value=99),
              ],
              string_value="protected",
          ),
          field_path="message_list",
          msg_after=TestMessage(string_value="protected"),
      ),
      dict(
          testcase_name="in_repeated_field",
          msg_before=TestMessage(
              int64_value=77,
              message_list=[
                  TestMessage(int64_value=1, string_value="protected2"),
                  TestMessage(int64_value=42, string_value="protected3"),
              ],
              string_value="protected",
          ),
          field_path="message_list.int64_value",
          msg_after=TestMessage(
              int64_value=77,
              message_list=[
                  TestMessage(string_value="protected2"),
                  TestMessage(string_value="protected3"),
              ],
              string_value="protected",
          ),
      ),
      dict(
          testcase_name="nested_inner_path",
          msg_before=TestMessage(
              message_value=TestMessage(
                  message_value=TestMessage(
                      foo_msg=TestMessage(
                          message_value=TestMessage(int64_value=42)
                      )
                  ),
                  string_value="protected2",
              ),
              string_value="protected",
          ),
          field_path="message_value.message_value",
          msg_after=TestMessage(
              message_value=TestMessage(string_value="protected2"),
              string_value="protected",
          ),
      ),
      dict(
          testcase_name="deep_nested_path",
          msg_before=TestMessage(
              message_list=[
                  TestMessage(
                      message_value=TestMessage(
                          foo_msg=TestMessage(
                              message_value=TestMessage(
                                  int64_value=42, string_value="protected4"
                              ),
                              string_value="protected3",
                          )
                      ),
                      string_value="protected2",
                  ),
              ],
              string_value="protected",
          ),
          field_path=(
              "message_list.message_value.foo_msg.message_value.int64_value"
          ),
          msg_after=TestMessage(
              message_list=[
                  TestMessage(
                      message_value=TestMessage(
                          foo_msg=TestMessage(
                              message_value=TestMessage(
                                  string_value="protected4"
                              ),
                              string_value="protected3",
                          )
                      ),
                      string_value="protected2",
                  ),
              ],
              string_value="protected",
          ),
      ),
      dict(
          testcase_name="oneof",
          msg_before=TestMessage(
              foo_msg=TestMessage(message_value=TestMessage(int64_value=42)),
              string_value="protected",
          ),
          field_path="foo_msg",
          msg_after=TestMessage(string_value="protected"),
      ),
      dict(
          testcase_name="other_oneof",
          msg_before=TestMessage(
              foo_msg=TestMessage(
                  message_value=TestMessage(
                      int64_value=42, string_value="protected3"
                  ),
                  string_value="protected2",
              ),
              string_value="protected",
          ),
          field_path="bar_msg",
          msg_after=TestMessage(
              foo_msg=TestMessage(
                  message_value=TestMessage(
                      int64_value=42, string_value="protected3"
                  ),
                  string_value="protected2",
              ),
              string_value="protected",
          ),
      ),
      dict(
          testcase_name="oneof_path",
          msg_before=TestMessage(
              message_list=[
                  TestMessage(
                      message_value=TestMessage(
                          foo_msg=TestMessage(
                              message_value=TestMessage(int64_value=42)
                          ),
                          string_value="protected3",
                      ),
                      string_value="protected2",
                  ),
              ],
              string_value="protected",
          ),
          field_path="message_list.message_value.foo_msg",
          msg_after=TestMessage(
              message_list=[
                  TestMessage(
                      message_value=TestMessage(string_value="protected3"),
                      string_value="protected2",
                  ),
              ],
              string_value="protected",
          ),
      ),
      dict(
          testcase_name="other_oneof_path",
          msg_before=TestMessage(
              message_list=[
                  TestMessage(
                      message_value=TestMessage(
                          foo_msg=TestMessage(
                              message_value=TestMessage(
                                  int64_value=42, string_value="protected4"
                              ),
                              string_value="protected3",
                          )
                      ),
                      string_value="protected2",
                  ),
              ],
              string_value="protected",
          ),
          field_path="message_list.message_value.bar_msg",
          msg_after=TestMessage(
              message_list=[
                  TestMessage(
                      message_value=TestMessage(
                          foo_msg=TestMessage(
                              message_value=TestMessage(
                                  int64_value=42, string_value="protected4"
                              ),
                              string_value="protected3",
                          )
                      ),
                      string_value="protected2",
                  ),
              ],
              string_value="protected",
          ),
      ),
  )
  def test_clear_field(self, msg_before, field_path, msg_after):
    compare._clear_field(msg_before, field_path)
    # This is a big chicken and egg as to test this result it is necessary to
    # compare protos, but _clear_field is part of assertProto2Equal.
    # _clear_field is not called as long as ignored_fields is not set, thus
    # this is fine.
    compare.assertProto2Equal(self, msg_before, msg_after)

  @parameterized.named_parameters(
      dict(
          testcase_name="invalid_field_path",
          msg_before=TestMessage(int64_value=42, string_value="protected"),
          field_path="int64_Xvalue",
      ),
      dict(
          testcase_name="invalid_nested_path",
          msg_before=TestMessage(
              int64_value=77,
              message_value=TestMessage(
                  int64_value=42, string_value="protected"
              ),
              string_value="protected2",
          ),
          field_path="message_value.int64_value.message_value",
      ),
      dict(
          testcase_name="invalid_field_in_path",
          msg_before=TestMessage(
              int64_value=77,
              message_value=TestMessage(
                  int64_value=42, string_value="protected"
              ),
              string_value="protected2",
          ),
          field_path="message_value.X.int64_value",
      ),
  )
  def test_clear_field_invalid_parameters(self, msg_before, field_path):
    with self.assertRaises(ValueError):
      compare._clear_field(msg_before, field_path)


class SortRepeatedFieldsTest(parameterized.TestCase):
  """Tests the _sort_repeated_fields function."""

  @parameterized.named_parameters(
      dict(
          testcase_name="basic_no_change",
          msg_before=TestMessage(int64_value=42, string_value="protected"),
          msg_after=TestMessage(int64_value=42, string_value="protected"),
          deduplicate=True,
      ),
      dict(
          testcase_name="nested_field_no_repeated",
          msg_before=TestMessage(
              message_value=TestMessage(
                  int64_value=42, string_value="protected"
              ),
          ),
          msg_after=TestMessage(
              message_value=TestMessage(
                  int64_value=42, string_value="protected"
              ),
          ),
          deduplicate=True,
      ),
      dict(
          testcase_name="map",
          msg_before=TestMessage(string_int32_map={"foo": 42, "bar": 99}),
          msg_after=TestMessage(string_int32_map={"foo": 42, "bar": 99}),
          deduplicate=True,
      ),
      dict(
          testcase_name="repeated_basic_field",
          msg_before=TestMessage(
              int32_list=[2, 1],
              int64_list=[2, 1],
              uint32_list=[2, 1],
              uint64_list=[2, 1],
              float_list=[2.0, 1.0],
              double_list=[2.0, 1.0],
              string_list=["b", "a"],
              cord_list=["b", "a"],
              bytes_list=[b"b", b"a"],
              bool_list=[True, False],
              enum_list=[TestMessage.TEST_ENUM_2, TestMessage.TEST_ENUM_1],
          ),
          msg_after=TestMessage(
              int32_list=[1, 2],
              int64_list=[1, 2],
              uint32_list=[1, 2],
              uint64_list=[1, 2],
              float_list=[1.0, 2.0],
              double_list=[1.0, 2.0],
              string_list=["a", "b"],
              cord_list=["a", "b"],
              bytes_list=[b"a", b"b"],
              bool_list=[False, True],
              enum_list=[TestMessage.TEST_ENUM_1, TestMessage.TEST_ENUM_2],
          ),
          deduplicate=True,
      ),
      dict(
          testcase_name="repeated_basic_field_with_duplicates_keep",
          msg_before=TestMessage(
              int32_list=[2, 1, 2, 1, 1, 1, 1],
              int64_list=[2, 1, 2, 1, 1, 1, 1],
              uint32_list=[2, 1, 2, 1, 1, 1, 1],
              uint64_list=[2, 1, 2, 1, 1, 1, 1],
              float_list=[1.0, 1.0, 2.0, 2.0, 1.0],
              double_list=[1.0, 1.0, 2.0, 2.0, 1.0],
              string_list=["b", "a", "b", "a"],
              cord_list=["b", "a", "b", "a"],
              bytes_list=[b"b", b"a", b"b", b"a"],
              bool_list=[True, False, False, True],
              enum_list=[
                  TestMessage.TEST_ENUM_2,
                  TestMessage.TEST_ENUM_1,
                  TestMessage.TEST_ENUM_2,
              ],
          ),
          msg_after=TestMessage(
              int32_list=[1, 1, 1, 1, 1, 2, 2],
              int64_list=[1, 1, 1, 1, 1, 2, 2],
              uint32_list=[1, 1, 1, 1, 1, 2, 2],
              uint64_list=[1, 1, 1, 1, 1, 2, 2],
              float_list=[1.0, 1.0, 1.0, 2.0, 2.0],
              double_list=[1.0, 1.0, 1.0, 2.0, 2.0],
              string_list=["a", "a", "b", "b"],
              cord_list=["a", "a", "b", "b"],
              bytes_list=[b"a", b"a", b"b", b"b"],
              bool_list=[False, False, True, True],
              enum_list=[
                  TestMessage.TEST_ENUM_1,
                  TestMessage.TEST_ENUM_2,
                  TestMessage.TEST_ENUM_2,
              ],
          ),
          deduplicate=False,
      ),
      dict(
          testcase_name="repeated_basic_field_with_duplicates_remove",
          msg_before=TestMessage(
              int32_list=[2, 1, 2, 1, 1, 1, 1],
              int64_list=[2, 1, 2, 1, 1, 1, 1],
              uint32_list=[2, 1, 2, 1, 1, 1, 1],
              uint64_list=[2, 1, 2, 1, 1, 1, 1],
              float_list=[1.0, 1.0, 2.0, 2.0, 1.0],
              double_list=[1.0, 1.0, 2.0, 2.0, 1.0],
              string_list=["b", "a", "b", "a"],
              cord_list=["b", "a", "b", "a"],
              bytes_list=[b"b", b"a", b"b", b"a"],
              bool_list=[True, False, False, True],
              enum_list=[
                  TestMessage.TEST_ENUM_2,
                  TestMessage.TEST_ENUM_1,
                  TestMessage.TEST_ENUM_2,
              ],
          ),
          msg_after=TestMessage(
              int32_list=[1, 2],
              int64_list=[1, 2],
              uint32_list=[1, 2],
              uint64_list=[1, 2],
              float_list=[1.0, 2.0],
              double_list=[1.0, 2.0],
              string_list=["a", "b"],
              cord_list=["a", "b"],
              bytes_list=[b"a", b"b"],
              bool_list=[False, True],
              enum_list=[TestMessage.TEST_ENUM_1, TestMessage.TEST_ENUM_2],
          ),
          deduplicate=True,
      ),
      dict(
          testcase_name="in_repeated_field",
          msg_before=TestMessage(
              message_list=[
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=1),
              ],
          ),
          msg_after=TestMessage(
              message_list=[
                  TestMessage(int64_value=1),
                  TestMessage(int64_value=2),
              ],
          ),
          deduplicate=True,
      ),
      dict(
          testcase_name="through_message_map",
          msg_before=TestMessage(
              string_message_map={
                  "foo": TestMessage(
                      message_list=[
                          TestMessage(int64_value=42),
                          TestMessage(int64_value=33),
                          TestMessage(int64_value=22),
                      ]
                  ),
                  "bar": TestMessage(int64_list=[3, 2, 1, 4]),
              }
          ),
          msg_after=TestMessage(
              string_message_map={
                  "foo": TestMessage(
                      message_list=[
                          TestMessage(int64_value=22),
                          TestMessage(int64_value=33),
                          TestMessage(int64_value=42),
                      ]
                  ),
                  "bar": TestMessage(int64_list=[1, 2, 3, 4]),
              }
          ),
          deduplicate=True,
      ),
      dict(
          testcase_name="nested_in_repeated_field",
          msg_before=TestMessage(
              message_list=[
                  TestMessage(int64_value=1, string_value="a"),
                  TestMessage(int64_value=2, string_value="b"),
              ],
          ),
          msg_after=TestMessage(
              message_list=[
                  TestMessage(int64_value=1, string_value="a"),
                  TestMessage(int64_value=2, string_value="b"),
              ],
          ),
          deduplicate=True,
      ),
      dict(
          testcase_name="nested_in_repeated_field2",
          msg_before=TestMessage(
              message_list=[
                  TestMessage(int64_value=1, string_value="b"),
                  TestMessage(int64_value=2, string_value="a"),
              ],
          ),
          msg_after=TestMessage(
              message_list=[
                  TestMessage(int64_value=1, string_value="b"),
                  TestMessage(int64_value=2, string_value="a"),
              ],
          ),
          deduplicate=True,
      ),
      dict(
          testcase_name="nested_in_repeated_field3",
          msg_before=TestMessage(
              message_list=[
                  TestMessage(int64_value=2, string_value="a"),
                  TestMessage(int64_value=1, string_value="b"),
              ],
          ),
          msg_after=TestMessage(
              message_list=[
                  TestMessage(int64_value=1, string_value="b"),
                  TestMessage(int64_value=2, string_value="a"),
              ],
          ),
          deduplicate=True,
      ),
      dict(
          testcase_name="nested_repeated_fields",
          msg_before=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=1),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=4),
                          TestMessage(int64_value=3),
                      ]
                  ),
              ],
          ),
          msg_after=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=3),
                          TestMessage(int64_value=4),
                      ]
                  ),
              ],
          ),
          deduplicate=True,
      ),
      dict(
          testcase_name="nested_repeated_fields_with_duplicates",
          msg_before=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=4),
                          TestMessage(int64_value=3),
                          TestMessage(int64_value=3),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=2),
                      ]
                  ),
              ],
          ),
          msg_after=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=3),
                          TestMessage(int64_value=4),
                      ]
                  ),
              ],
          ),
          deduplicate=True,
      ),
      dict(
          testcase_name="nested_repeated_fields_with_duplicates_keep",
          msg_before=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=4),
                          TestMessage(int64_value=3),
                          TestMessage(int64_value=3),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=2),
                      ]
                  ),
              ],
          ),
          msg_after=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=3),
                          TestMessage(int64_value=3),
                          TestMessage(int64_value=4),
                      ]
                  ),
              ],
          ),
          deduplicate=False,
      ),
  )
  def test_sort_fields(self, msg_before, msg_after, deduplicate):
    compare._sort_repeated_fields(msg_before, deduplicate=deduplicate)
    compare.assertProto2Equal(self, msg_before, msg_after)


class EquializeFloatsTest(parameterized.TestCase):
  """Tests the _equalize_floats_in_tolerance function."""

  @parameterized.named_parameters(
      dict(
          testcase_name="basic_no_change",
          msg=TestMessage(int64_value=42, string_value="protected"),
          msg_other=TestMessage(int64_value=42, string_value="protected"),
          rtol=0.1,
          msg_after=TestMessage(int64_value=42, string_value="protected"),
      ),
      dict(
          testcase_name="float_smaller_to_larger",
          msg=TestMessage(float_value=0.95),
          msg_other=TestMessage(float_value=1.0),
          rtol=0.1,
          msg_after=TestMessage(float_value=1.0),
      ),
      dict(
          testcase_name="double",
          msg=TestMessage(double_value=0.95),
          msg_other=TestMessage(double_value=1.0),
          rtol=0.1,
          msg_after=TestMessage(double_value=1.0),
      ),
      dict(
          testcase_name="float_larger_to_smaller",
          msg=TestMessage(float_value=1.0),
          msg_other=TestMessage(float_value=0.95),
          rtol=0.1,
          msg_after=TestMessage(float_value=0.95),
      ),
      dict(
          testcase_name="out_of_rtol",
          msg=TestMessage(float_value=0.85),
          msg_other=TestMessage(float_value=1.0),
          rtol=0.1,
          msg_after=TestMessage(float_value=0.85),
      ),
      dict(
          testcase_name="negative",
          msg=TestMessage(float_value=-0.95),
          msg_other=TestMessage(float_value=-1.0),
          rtol=0.1,
          msg_after=TestMessage(float_value=-1.0),
      ),
      dict(
          testcase_name="negative_out_of_rtol",
          msg=TestMessage(float_value=-0.85),
          msg_other=TestMessage(float_value=-1.0),
          rtol=0.1,
          msg_after=TestMessage(float_value=-0.85),
      ),
      dict(
          testcase_name="mixed_signs",
          msg=TestMessage(float_value=-0.05),
          msg_other=TestMessage(float_value=1.0),
          rtol=1.1,
          msg_after=TestMessage(float_value=1.0),
      ),
      dict(
          testcase_name="mixed_signs_out_of_rtol",
          msg=TestMessage(float_value=-0.15),
          msg_other=TestMessage(float_value=1.0),
          rtol=1.1,
          msg_after=TestMessage(float_value=-0.15),
      ),
      dict(
          testcase_name="unset",
          msg=TestMessage(),
          msg_other=TestMessage(float_value=1.0),
          rtol=1.1,
          msg_after=TestMessage(),
      ),
      dict(
          testcase_name="unset_other",
          msg=TestMessage(float_value=1.0),
          msg_other=TestMessage(),
          rtol=1.1,
          msg_after=TestMessage(float_value=1.0),
      ),
      dict(
          testcase_name="zero_set",
          msg=TestMessage(float_value=0.0),
          msg_other=TestMessage(float_value=1.0),
          rtol=1.1,
          msg_after=TestMessage(),
      ),
      dict(
          testcase_name="zero_set_other",
          msg=TestMessage(float_value=1.0),
          msg_other=TestMessage(float_value=0.0),
          rtol=1.1,
          msg_after=TestMessage(float_value=1.0),
      ),
      dict(
          testcase_name="optional_unset",
          msg=TestMessage(),
          msg_other=TestMessage(optional_float_value=1.0),
          rtol=1.1,
          msg_after=TestMessage(),
      ),
      dict(
          testcase_name="optional_unset_other",
          msg=TestMessage(optional_float_value=1.0),
          msg_other=TestMessage(),
          rtol=1.1,
          msg_after=TestMessage(optional_float_value=1.0),
      ),
      dict(
          testcase_name="optional_set",
          msg=TestMessage(optional_float_value=0.0),
          msg_other=TestMessage(optional_float_value=1.0),
          rtol=1.1,
          msg_after=TestMessage(optional_float_value=1.0),
      ),
      dict(
          testcase_name="optional_set_other",
          msg=TestMessage(optional_float_value=1.0),
          msg_other=TestMessage(optional_float_value=0.0),
          rtol=1.1,
          msg_after=TestMessage(optional_float_value=0.0),
      ),
      dict(
          testcase_name="float_list",
          msg=TestMessage(
              float_list=[
                  5.0,
                  1.0,
                  10.0,
                  5.0,
                  1.0,
                  10.0,
              ]
          ),
          msg_other=TestMessage(
              float_list=[
                  4.95,
                  0.95,
                  9.95,
                  4.45,
                  0.85,
                  8.95,
              ]
          ),
          rtol=0.1,
          msg_after=TestMessage(
              float_list=[
                  4.95,
                  0.95,
                  9.95,
                  5.0,
                  1.0,
                  10.0,
              ]
          ),
      ),
      dict(
          testcase_name="double_list",
          msg=TestMessage(
              double_list=[
                  5.0,
                  1.0,
                  10.0,
                  5.0,
                  1.0,
                  10.0,
              ]
          ),
          msg_other=TestMessage(
              double_list=[
                  4.95,
                  0.95,
                  9.95,
                  4.45,
                  0.85,
                  8.95,
              ]
          ),
          rtol=0.1,
          msg_after=TestMessage(
              double_list=[
                  4.95,
                  0.95,
                  9.95,
                  5.0,
                  1.0,
                  10.0,
              ]
          ),
      ),
      dict(
          testcase_name="list_extra_values",
          msg=TestMessage(
              float_list=[
                  5.0,
                  1.0,
                  10.0,
                  5.0,
                  1.0,
                  10.0,
              ]
          ),
          msg_other=TestMessage(
              float_list=[
                  4.95,
                  0.95,
                  9.95,
                  4.45,
                  0.85,
                  8.95,
                  70.0,
                  80.0,
              ]
          ),
          rtol=0.1,
          msg_after=TestMessage(
              float_list=[
                  4.95,
                  0.95,
                  9.95,
                  5.0,
                  1.0,
                  10.0,
              ]
          ),
      ),
      dict(
          testcase_name="list_less_values",
          msg=TestMessage(
              float_list=[
                  5.0,
                  1.0,
                  10.0,
                  5.0,
                  1.0,
                  10.0,
                  70.0,
                  80.0,
              ]
          ),
          msg_other=TestMessage(
              float_list=[
                  4.95,
                  0.95,
                  9.95,
                  4.45,
                  0.85,
                  8.95,
              ]
          ),
          rtol=0.1,
          msg_after=TestMessage(
              float_list=[
                  4.95,
                  0.95,
                  9.95,
                  5.0,
                  1.0,
                  10.0,
                  70.0,
                  80.0,
              ]
          ),
      ),
      dict(
          testcase_name="map_to_float",
          msg=TestMessage(
              string_float_map={
                  "foo": 5.0,
                  "bar": 1.0,
                  "baz": 10.0,
                  "foofoo": 50.0,
                  "foobar": 100.0,
                  "foobaz": 500.0,
                  "out_foo": 5.0,
                  "out_bar": 1.0,
                  "out_baz": 10.0,
                  "out_foofoo": 50.0,
                  "out_foobar": 100.0,
                  "out_foobaz": 500.0,
                  "msg_entry": 777.0,
              }
          ),
          msg_other=TestMessage(
              string_float_map={
                  "foo": 4.95,
                  "bar": 0.95,
                  "baz": 9.95,
                  "foofoo": 49.5,
                  "foobar": 99.5,
                  "foobaz": 499.5,
                  "out_foo": 4.45,
                  "out_bar": 0.85,
                  "out_baz": 8.95,
                  "out_foofoo": 44.5,
                  "out_foobar": 89.5,
                  "out_foobaz": 449.5,
                  "other_entry": 777.7,
              }
          ),
          rtol=0.1,
          msg_after=TestMessage(
              string_float_map={
                  "foo": 4.95,
                  "bar": 0.95,
                  "baz": 9.95,
                  "foofoo": 49.5,
                  "foobar": 99.5,
                  "foobaz": 499.5,
                  "out_foo": 5.0,
                  "out_bar": 1.0,
                  "out_baz": 10.0,
                  "out_foofoo": 50.0,
                  "out_foobar": 100.0,
                  "out_foobaz": 500.0,
                  "msg_entry": 777.0,
              }
          ),
      ),
      dict(
          testcase_name="map_to_double",
          msg=TestMessage(
              string_double_map={
                  "foo": 5.0,
                  "bar": 1.0,
                  "baz": 10.0,
                  "foofoo": 50.0,
                  "foobar": 100.0,
                  "foobaz": 500.0,
                  "out_foo": 5.0,
                  "out_bar": 1.0,
                  "out_baz": 10.0,
                  "out_foofoo": 50.0,
                  "out_foobar": 100.0,
                  "out_foobaz": 500.0,
                  "msg_entry": 777.0,
              }
          ),
          msg_other=TestMessage(
              string_double_map={
                  "foo": 4.95,
                  "bar": 0.95,
                  "baz": 9.95,
                  "foofoo": 49.5,
                  "foobar": 99.5,
                  "foobaz": 499.5,
                  "out_foo": 4.45,
                  "out_bar": 0.85,
                  "out_baz": 8.95,
                  "out_foofoo": 44.5,
                  "out_foobar": 89.5,
                  "out_foobaz": 449.5,
                  "other_entry": 777.7,
              }
          ),
          rtol=0.1,
          msg_after=TestMessage(
              string_double_map={
                  "foo": 4.95,
                  "bar": 0.95,
                  "baz": 9.95,
                  "foofoo": 49.5,
                  "foobar": 99.5,
                  "foobaz": 499.5,
                  "out_foo": 5.0,
                  "out_bar": 1.0,
                  "out_baz": 10.0,
                  "out_foofoo": 50.0,
                  "out_foobar": 100.0,
                  "out_foobaz": 500.0,
                  "msg_entry": 777.0,
              }
          ),
      ),
      dict(
          testcase_name="nested_message",
          msg=TestMessage(
              message_value=TestMessage(float_value=1.0),
          ),
          msg_other=TestMessage(
              message_value=TestMessage(float_value=0.95),
          ),
          rtol=0.1,
          msg_after=TestMessage(
              message_value=TestMessage(float_value=0.95),
          ),
      ),
      dict(
          testcase_name="nested_message_oneof",
          msg=TestMessage(
              foo_msg=TestMessage(float_value=1.0),
          ),
          msg_other=TestMessage(
              foo_msg=TestMessage(float_value=0.95),
          ),
          rtol=0.1,
          msg_after=TestMessage(
              foo_msg=TestMessage(float_value=0.95),
          ),
      ),
      dict(
          testcase_name="in_repeated_field",
          msg=TestMessage(
              message_list=[
                  TestMessage(float_value=1.0),
                  TestMessage(float_value=5.0),
                  TestMessage(float_value=10.0),
              ],
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(float_value=0.95),
                  TestMessage(float_value=4.45),
                  TestMessage(float_value=9.5),
                  TestMessage(float_value=77.0),
              ],
          ),
          rtol=0.1,
          msg_after=TestMessage(
              message_list=[
                  TestMessage(float_value=0.95),
                  TestMessage(float_value=5.0),
                  TestMessage(float_value=9.5),
              ],
          ),
      ),
      dict(
          testcase_name="nested_repeated_fields",
          msg=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=5.0),
                          TestMessage(float_value=77.0),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=2.0),
                          TestMessage(float_value=4.0),
                      ]
                  ),
              ],
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=0.95),
                          TestMessage(float_value=4.45),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=1.75),
                          TestMessage(float_value=3.7),
                          TestMessage(float_value=76.5),
                      ]
                  ),
              ],
          ),
          rtol=0.1,
          msg_after=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=0.95),
                          TestMessage(float_value=5.0),
                          TestMessage(float_value=77.0),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=2.0),
                          TestMessage(float_value=3.7),
                      ]
                  ),
              ],
          ),
      ),
      dict(
          testcase_name="through_message_map",
          msg=TestMessage(
              string_message_map={
                  "foo": TestMessage(float_value=5.0),
                  "bar": TestMessage(float_value=1.0),
                  "baz": TestMessage(float_value=10.0),
                  "foofoo": TestMessage(float_value=50.0),
                  "foobar": TestMessage(float_value=100.0),
                  "foobaz": TestMessage(float_value=500.0),
                  "out_foo": TestMessage(float_value=5.0),
                  "out_bar": TestMessage(float_value=1.0),
                  "out_baz": TestMessage(float_value=10.0),
                  "out_foofoo": TestMessage(float_value=50.0),
                  "out_foobar": TestMessage(float_value=100.0),
                  "out_foobaz": TestMessage(float_value=500.0),
                  "msg_entry": TestMessage(float_value=777.0),
              }
          ),
          msg_other=TestMessage(
              string_message_map={
                  "foo": TestMessage(float_value=4.95),
                  "bar": TestMessage(float_value=0.95),
                  "baz": TestMessage(float_value=9.95),
                  "foofoo": TestMessage(float_value=49.5),
                  "foobar": TestMessage(float_value=99.5),
                  "foobaz": TestMessage(float_value=499.5),
                  "out_foo": TestMessage(float_value=4.45),
                  "out_bar": TestMessage(float_value=0.85),
                  "out_baz": TestMessage(float_value=8.95),
                  "out_foofoo": TestMessage(float_value=44.5),
                  "out_foobar": TestMessage(float_value=89.5),
                  "out_foobaz": TestMessage(float_value=449.5),
                  "other_entry": TestMessage(float_value=777.7),
              }
          ),
          rtol=0.1,
          msg_after=TestMessage(
              string_message_map={
                  "foo": TestMessage(float_value=4.95),
                  "bar": TestMessage(float_value=0.95),
                  "baz": TestMessage(float_value=9.95),
                  "foofoo": TestMessage(float_value=49.5),
                  "foobar": TestMessage(float_value=99.5),
                  "foobaz": TestMessage(float_value=499.5),
                  "out_foo": TestMessage(float_value=5.0),
                  "out_bar": TestMessage(float_value=1.0),
                  "out_baz": TestMessage(float_value=10.0),
                  "out_foofoo": TestMessage(float_value=50.0),
                  "out_foobar": TestMessage(float_value=100.0),
                  "out_foobaz": TestMessage(float_value=500.0),
                  "msg_entry": TestMessage(float_value=777.0),
              }
          ),
      ),
  )
  def test_equalize_floats_in_tolerance(self, msg, msg_other, rtol, msg_after):
    msg_other_before = copy.deepcopy(msg_other)
    compare._equalize_floats_in_tolerance(msg, msg_other, rtol)

    # Only values in msg are supposed to be changed. Thus msg_other should be
    # unchanged.
    compare.assertProto2Equal(self, msg_other, msg_other_before)
    compare.assertProto2Equal(self, msg, msg_after)


class CompareTest(parameterized.TestCase):
  """Tests that the compare module works."""

  @parameterized.named_parameters(
      dict(testcase_name="basic_compare", msg=TestMessage(int64_value=42)),
      dict(
          testcase_name="nested_message",
          msg=TestMessage(
              int64_value=42,
              message_value=TestMessage(string_value="foo"),
          ),
      ),
      dict(
          testcase_name="complex_message",
          msg=TestMessage(
              int64_value=42,
              message_value=TestMessage(
                  string_value="foo", message_value=TestMessage(bool_value=True)
              ),
              optional_string_value="bar",
              bar="baz",
              enum_value=TestMessage.TEST_ENUM_2,
              bar_msg=TestMessage(uint32_value=77),
              message_list=[
                  TestMessage(float_value=1.0),
                  TestMessage(float_value=2.0),
                  TestMessage(double_value=3.0),
              ],
              string_int32_map={"foo": 1, "bar": 2},
          ),
      ),
      dict(
          testcase_name="compare_ignored_fields",
          msg=TestMessage(int64_value=42),
          msg_other=TestMessage(int64_value=99),
          ignored_fields=["int64_value"],
      ),
      dict(
          testcase_name="compare_nested_ignored_fields",
          msg=TestMessage(message_value=TestMessage(int64_value=42)),
          msg_other=TestMessage(message_value=TestMessage(int64_value=99)),
          ignored_fields=["message_value.int64_value"],
      ),
      dict(
          testcase_name="compare_map_ignored_fields",
          msg=TestMessage(string_int32_map={"foo": 42}),
          msg_other=TestMessage(string_int32_map={"bar": 42}),
          ignored_fields=["string_int32_map"],
      ),
      dict(
          testcase_name="compare_repeated_ignored_fields",
          msg=TestMessage(message_list=[TestMessage(int64_value=42)]),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int64_value=42),
                  TestMessage(int64_value=99),
              ]
          ),
          ignored_fields=["message_list"],
      ),
      dict(
          testcase_name="compare_in_repeated_ignored_fields",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=1),
                  TestMessage(int64_value=42),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int64_value=1),
                  TestMessage(int64_value=99),
              ]
          ),
          ignored_fields=["message_list.int64_value"],
      ),
      dict(
          testcase_name="compare_nested_paths_shorter_ignore_path",
          msg=TestMessage(
              message_value=TestMessage(
                  message_value=TestMessage(
                      foo_msg=TestMessage(
                          message_value=TestMessage(int64_value=42)
                      )
                  )
              )
          ),
          msg_other=TestMessage(
              message_value=TestMessage(
                  message_value=TestMessage(
                      foo_msg=TestMessage(
                          message_value=TestMessage(int64_value=99)
                      )
                  )
              )
          ),
          ignored_fields=["message_value.message_value"],
      ),
      dict(
          testcase_name="compare_nested_paths_ignored_fields",
          msg=TestMessage(
              message_list=[
                  TestMessage(
                      message_value=TestMessage(
                          foo_msg=TestMessage(
                              message_value=TestMessage(int64_value=42)
                          )
                      )
                  ),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(
                      message_value=TestMessage(
                          foo_msg=TestMessage(
                              message_value=TestMessage(int64_value=99)
                          )
                      )
                  ),
              ]
          ),
          ignored_fields=[
              "message_list.message_value.foo_msg.message_value.int64_value"
          ],
      ),
      dict(
          testcase_name="compare_switched_oneof_ignored_fields",
          msg=TestMessage(
              message_list=[
                  TestMessage(
                      message_value=TestMessage(
                          foo_msg=TestMessage(
                              message_value=TestMessage(int64_value=42)
                          )
                      )
                  ),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(
                      message_value=TestMessage(
                          bar_msg=TestMessage(
                              message_value=TestMessage(int64_value=42)
                          )
                      )
                  ),
              ]
          ),
          ignored_fields=[
              "message_list.message_value.foo_msg",
              "message_list.message_value.bar_msg",
          ],
      ),
      dict(
          testcase_name="basic_message_unaffected_by_rtol",
          msg=TestMessage(int32_value=4),
          msg_other=TestMessage(int32_value=4),
          rtol=0.5,
      ),
      dict(
          testcase_name="same_float_with_rtol",
          msg=TestMessage(float_value=4.0),
          msg_other=TestMessage(float_value=4.0),
          rtol=0.5,
      ),
      dict(
          testcase_name="diff_float_rtol_smaller",
          msg=TestMessage(float_value=4.0),
          msg_other=TestMessage(float_value=2.1),
          rtol=0.5,
      ),
      dict(
          testcase_name="diff_float_rtol_larger",
          msg=TestMessage(float_value=3.1),
          msg_other=TestMessage(float_value=6.0),
          rtol=0.5,
      ),
      dict(
          testcase_name="diff_double_rtol_smaller",
          msg=TestMessage(double_value=4.0),
          msg_other=TestMessage(double_value=2.1),
          rtol=0.5,
      ),
      dict(
          testcase_name="diff_double_rtol_larger",
          msg=TestMessage(double_value=3.1),
          msg_other=TestMessage(double_value=6.0),
          rtol=0.5,
      ),
      dict(
          testcase_name="float_rtol_not_set_both",
          msg=TestMessage(),
          msg_other=TestMessage(),
          rtol=1.1,
      ),
      # An optional value has explicit presence and can therefore differentiate
      # between an unset value and a value set to 0.0.
      dict(
          testcase_name="float_rtol_optional_zero_to_near_zero",
          msg=TestMessage(optional_float_value=0.0),
          msg_other=TestMessage(optional_float_value=0.2),
          rtol=1.1,
      ),
      dict(
          testcase_name="float_rtol_optional_near_zero_to_zero",
          msg=TestMessage(optional_float_value=0.2),
          msg_other=TestMessage(optional_float_value=0.0),
          rtol=1.1,
      ),
      dict(
          testcase_name="float_list_rtol_list1",
          msg=TestMessage(float_list=[4.0, 2.0, 2.0]),
          msg_other=TestMessage(float_list=[4.05, 1.95, 2.05]),
          rtol=0.1,
      ),
      dict(
          testcase_name="float_list_rtol_list2",
          msg=TestMessage(float_list=[4.0, 2.0, 2.05]),
          msg_other=TestMessage(float_list=[4.05, 1.95, 2.0]),
          rtol=0.1,
      ),
      dict(
          testcase_name="float_list_rtol_list3",
          msg=TestMessage(float_list=[4.0, 1.95, 2.0]),
          msg_other=TestMessage(float_list=[4.05, 2.0, 2.05]),
          rtol=0.1,
      ),
      dict(
          testcase_name="float_list_rtol_list4",
          msg=TestMessage(float_list=[4.0, 1.95, 2.05]),
          msg_other=TestMessage(float_list=[4.05, 2.0, 2.0]),
          rtol=0.1,
      ),
      dict(
          testcase_name="message_list_rtol",
          msg=TestMessage(
              message_list=[
                  TestMessage(float_value=11.0),
                  TestMessage(float_value=1.0),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(float_value=10.1),
                  TestMessage(float_value=0.95),
              ]
          ),
          rtol=0.1,
      ),
      dict(
          testcase_name="in_map_rtol",
          msg=TestMessage(
              string_message_map={
                  "foo": TestMessage(double_list=[0.95, 10.1]),
                  "bar": TestMessage(float_value=1.0, float_list=[1.0, 1.01]),
              }
          ),
          msg_other=TestMessage(
              string_message_map={
                  "foo": TestMessage(double_list=[1.0, 11.0]),
                  "bar": TestMessage(float_value=0.95, float_list=[0.95, 0.97]),
              }
          ),
          rtol=0.1,
      ),
      dict(
          testcase_name="complex_message_rtol",
          msg=TestMessage(
              int64_value=42,
              message_value=TestMessage(
                  string_value="foo",
                  message_value=TestMessage(
                      float_value=1.0,
                      bool_value=True,
                  ),
              ),
              optional_string_value="bar",
              bar="baz",
              enum_value=TestMessage.TEST_ENUM_2,
              bar_msg=TestMessage(double_value=1.0),
              message_list=[
                  TestMessage(float_value=1.0),
                  TestMessage(string_value="something"),
                  TestMessage(float_value=10.0),
                  TestMessage(double_value=20.0),
                  TestMessage(string_value="more"),
              ],
          ),
          msg_other=TestMessage(
              int64_value=42,
              message_value=TestMessage(
                  string_value="foo",
                  message_value=TestMessage(
                      float_value=0.95,
                      bool_value=True,
                  ),
              ),
              optional_string_value="bar",
              bar="baz",
              enum_value=TestMessage.TEST_ENUM_2,
              bar_msg=TestMessage(double_value=0.95),
              message_list=[
                  TestMessage(float_value=0.95),
                  TestMessage(string_value="something"),
                  TestMessage(float_value=9.5),
                  TestMessage(double_value=19.5),
                  TestMessage(string_value="more"),
              ],
          ),
          rtol=0.1,
      ),
      dict(
          testcase_name="message_list_multiple_floats_rtol",
          msg=TestMessage(
              message_list=[
                  TestMessage(float_value=10.0, double_value=1.0),
                  TestMessage(float_value=20.0, double_value=1.1),
              ],
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(float_value=10.1, double_value=1.1),
                  TestMessage(float_value=20.2, double_value=1.0),
              ],
          ),
          rtol=0.1,
      ),
      dict(
          testcase_name="message_list_multiple_floats_rtol2",
          msg=TestMessage(
              message_list=[
                  TestMessage(float_value=1.0, double_value=10.0),
                  TestMessage(float_value=1.1, double_value=20.0),
              ],
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(float_value=1.1, double_value=10.1),
                  TestMessage(float_value=1.0, double_value=20.2),
              ],
          ),
          rtol=0.1,
      ),
      dict(
          testcase_name="accepts_textproto",
          msg="int64_value: 42",
          msg_other=TestMessage(int64_value=42),
      ),
      dict(
          testcase_name="accepts_empty_textproto",
          msg="",
          msg_other=TestMessage(),
      ),
      dict(
          testcase_name="accepts_complex_textproto",
          msg=r"""
              int64_value: 42
              message_value: {
                string_value: "foo"
                message_value: {
                  float_value: 0.95
                  bool_value: True
                }
              }
              optional_string_value: "bar"
              bar: "baz"
              bar_msg: { double_value: 0.95 }
              message_list {
                float_value: 0.95
              }
              message_list {
                string_value: "something"
              }
              message_list {
                float_value: 9.5
              }
              message_list {
                double_value: 19.5
              }
              message_list {
                string_value: "more"
              }
          """,
          msg_other=TestMessage(
              int64_value=42,
              message_value=TestMessage(
                  string_value="foo",
                  message_value=TestMessage(
                      float_value=0.95,
                      bool_value=True,
                  ),
              ),
              optional_string_value="bar",
              bar="baz",
              bar_msg=TestMessage(double_value=0.95),
              message_list=[
                  TestMessage(float_value=0.95),
                  TestMessage(string_value="something"),
                  TestMessage(float_value=9.5),
                  TestMessage(double_value=19.5),
                  TestMessage(string_value="more"),
              ],
          ),
      ),
  )
  def test_assert_proto2_equal_compares(
      self,
      msg,
      msg_other=None,
      ignored_fields=None,
      rtol=None,
  ):
    """Compares msg with msg_other assuming they are equal."""
    if msg_other is None:
      msg_other = copy.deepcopy(msg)
    compare.assertProto2Equal(
        self, msg, msg_other, ignored_fields=ignored_fields, rtol=rtol
    )
    if not isinstance(msg, str | bytes):
      compare.assertProto2Equal(
          self, msg_other, msg, ignored_fields=ignored_fields, rtol=rtol
      )
    if rtol is None:
      # If messages are equal they must contain the same elements
      compare.assertProto2SameElements(
          self,
          msg,
          msg_other,
          ignored_fields=ignored_fields,
          keep_duplicate_values=True,
      )
      if not isinstance(msg, str | bytes):
        compare.assertProto2SameElements(
            self,
            msg_other,
            msg,
            ignored_fields=ignored_fields,
            keep_duplicate_values=True,
        )
      # If messages are equal than one must contain the other and vice versa
      compare.assertProto2Contains(
          self, msg, msg_other, ignored_fields=ignored_fields
      )
      if not isinstance(msg, str | bytes):
        compare.assertProto2Contains(
            self, msg_other, msg, ignored_fields=ignored_fields
        )

  @parameterized.named_parameters(
      dict(
          testcase_name="failed_compare",
          msg=TestMessage(int64_value=42),
          msg_other=TestMessage(int64_value=99),
          expected_error=f"""
\\- int64_value: 42
{mismatch_line_re}
\\+ int64_value: 99
{mismatch_line_re}
""",
      ),
      dict(
          testcase_name="nested_message_compare",
          msg=TestMessage(
              int64_value=42,
              message_value=TestMessage(string_value="foo"),
          ),
          msg_other=TestMessage(
              int64_value=42,
              message_value=TestMessage(string_value="bar"),
          ),
          expected_error=f"""
  int64_value: 42
  message_value {{
\\-   string_value: "foo"
{mismatch_line_re}
\\+   string_value: "bar"
{mismatch_line_re}
 *}}""",
      ),
      dict(
          testcase_name="nested_messages_multiple_differences",
          msg=TestMessage(
              int64_value=42,
              message_value=TestMessage(string_value="foo"),
          ),
          msg_other=TestMessage(
              int64_value=99,
              message_value=TestMessage(string_value="bar"),
          ),
          expected_error=f"""
\\- int64_value: 42
{mismatch_line_re}
\\+ int64_value: 99
{mismatch_line_re}
  message_value {{
\\-   string_value: "foo"
{mismatch_line_re}
\\+   string_value: "bar"
{mismatch_line_re}
  }}""",
      ),
      dict(
          testcase_name="complex_message",
          msg=TestMessage(
              int64_value=42,
              message_value=TestMessage(
                  string_value="foo", message_value=TestMessage(bool_value=True)
              ),
              optional_string_value="bar",
              bar="baz",
              enum_value=TestMessage.TEST_ENUM_2,
              bar_msg=TestMessage(uint32_value=77),
              message_list=[
                  TestMessage(float_value=1.0),
                  TestMessage(float_value=2.0),
                  TestMessage(double_value=3.0),
              ],
              string_int32_map={"foo": 1, "bar": 2},
          ),
          msg_other=TestMessage(
              int64_value=42,
              message_value=TestMessage(
                  string_value="foo", message_value=TestMessage(bool_value=True)
              ),
              optional_string_value="bar",
              bar="baz",
              enum_value=TestMessage.TEST_ENUM_1,
              bar_msg=TestMessage(uint32_value=77),
              message_list=[
                  TestMessage(float_value=1.0),
                  TestMessage(float_value=2.6),
                  TestMessage(double_value=3.0),
              ],
              string_int32_map={"baz": 1, "bar": 3},
          ),
          expected_error=f"""(?s)
\\- enum_value: TEST_ENUM_2
{mismatch_line_re}
\\+ enum_value: TEST_ENUM_1
{mismatch_line_re}
{non_mismatch_lines}
  message_list {{
\\-   float_value: 2.0
{mismatch_line_re}
\\+   float_value: 2.6
{mismatch_line_re}
  }}
{non_mismatch_lines}
  string_int32_map {{
    key: "bar"
\\-   value: 2
{mismatch_line_re}
\\+   value: 3
{mismatch_line_re}
  }}
  string_int32_map {{
\\-   key: "foo"
{mismatch_line_re}
\\+   key: "baz"
{mismatch_line_re}
    value: 1
  }}
{non_mismatch_lines}
""",
      ),
      dict(
          testcase_name="list_added_item",
          msg=TestMessage(int32_list=[1, 2, 4]),
          msg_other=TestMessage(int32_list=[1, 2, 3, 4]),
          expected_error=r"""
  int32_list: 1
  int32_list: 2
\+ int32_list: 3
  int32_list: 4
""",
      ),
      dict(
          testcase_name="list_missing_item",
          msg=TestMessage(int32_list=[1, 2, 3, 4]),
          msg_other=TestMessage(int32_list=[1, 2, 4]),
          expected_error="""
  int32_list: 1
  int32_list: 2
- int32_list: 3
  int32_list: 4
""",
      ),
      dict(
          testcase_name="message_list_added_item",
          msg=TestMessage(
              message_list=[
                  TestMessage(int32_value=1),
                  TestMessage(int32_value=2),
                  TestMessage(int32_value=4),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int32_value=1),
                  TestMessage(int32_value=2),
                  TestMessage(int32_value=3),
                  TestMessage(int32_value=4),
              ]
          ),
          expected_error=r"""
  message_list {
    int32_value: 1
  }
  message_list {
    int32_value: 2
  }
  message_list {
\+   int32_value: 3
\+ }
\+ message_list {
    int32_value: 4
  }
""",
      ),
      dict(
          testcase_name="message_list_missing_item",
          msg=TestMessage(
              message_list=[
                  TestMessage(int32_value=1),
                  TestMessage(int32_value=2),
                  TestMessage(int32_value=3),
                  TestMessage(int32_value=4),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int32_value=1),
                  TestMessage(int32_value=2),
                  TestMessage(int32_value=4),
              ]
          ),
          expected_error=r"""
  message_list {
    int32_value: 1
  }
  message_list {
    int32_value: 2
  }
  message_list {
\-   int32_value: 3
\- }
\- message_list {
    int32_value: 4
  }
""",
      ),
      dict(
          testcase_name="message_list_diffing_item",
          msg=TestMessage(
              message_list=[
                  TestMessage(int32_value=1),
                  TestMessage(),
                  TestMessage(int32_value=3),
                  TestMessage(int32_value=4),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int32_value=1),
                  TestMessage(int32_value=2),
                  TestMessage(),
                  TestMessage(int32_value=4),
              ]
          ),
          expected_error=r"""
  message_list {
    int32_value: 1
  }
  message_list {
\+   int32_value: 2
  }
  message_list {
\-   int32_value: 3
  }
  message_list {
    int32_value: 4
  }
""",
      ),
      dict(
          testcase_name="compare_switched_oneof_ignored_one_oneof",
          msg=TestMessage(
              message_list=[
                  TestMessage(
                      message_value=TestMessage(
                          foo_msg=TestMessage(
                              message_value=TestMessage(int64_value=42)
                          )
                      )
                  ),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(
                      message_value=TestMessage(
                          bar_msg=TestMessage(
                              message_value=TestMessage(int64_value=42)
                          )
                      )
                  ),
              ]
          ),
          ignored_fields=[
              "message_list.message_value.bar_msg",
          ],
          expected_error=r"""
  message_list {
    message_value {
-     foo_msg {
-       message_value {
-         int64_value: 42
-       }
-     }
    }
  }
""",
      ),
      dict(
          testcase_name="diff_float_rtol_too_small",
          msg=TestMessage(float_value=4.0),
          msg_other=TestMessage(float_value=1.9),
          rtol=0.5,
          expected_error=f"""
\\- float_value: 4.0
{mismatch_line_re}
\\+ float_value: 1.9
{mismatch_line_re}
""",
      ),
      dict(
          testcase_name="diff_float_rtol_too_large",
          msg=TestMessage(float_value=3.0),
          msg_other=TestMessage(float_value=6.2),
          rtol=0.5,
          expected_error=f"""
\\- float_value: 3.0
{mismatch_line_re}
\\+ float_value: 6.2
{mismatch_line_re}
""",
      ),
      dict(
          testcase_name="diff_double_rtol_too_small",
          msg=TestMessage(double_value=4.0),
          msg_other=TestMessage(double_value=1.9),
          rtol=0.5,
          expected_error=f"""
\\- double_value: 4.0
{mismatch_line_re}
\\+ double_value: 1.9
{mismatch_line_re}
""",
      ),
      dict(
          testcase_name="diff_double_rtol_too_large",
          msg=TestMessage(double_value=3.0),
          msg_other=TestMessage(double_value=6.2),
          rtol=0.5,
          expected_error=f"""
\\- double_value: 3.0
{mismatch_line_re}
\\+ double_value: 6.2
{mismatch_line_re}
""",
      ),
      dict(
          testcase_name="float_rtol_not_set",
          msg=TestMessage(),
          msg_other=TestMessage(float_value=4.2),
          rtol=1.1,
          expected_error="""
\\+ float_value: 4.2
""",
      ),
      dict(
          testcase_name="float_rtol_not_set_other",
          msg=TestMessage(float_value=4.2),
          msg_other=TestMessage(),
          rtol=1.1,
          expected_error="""
\\- float_value: 4.2
""",
      ),
      dict(
          testcase_name="float_rtol_not_set_near_zero",
          msg=TestMessage(),
          msg_other=TestMessage(float_value=0.2),
          rtol=1.1,
          expected_error="""
\\+ float_value: 0.2
""",
      ),
      dict(
          testcase_name="float_rtol_not_set_other_near_zero",
          msg=TestMessage(float_value=0.2),
          msg_other=TestMessage(),
          rtol=1.1,
          expected_error="""
\\- float_value: 0.2
""",
      ),
      # comparing to 0.0 will fail the same way that comparing to an unset value
      # fails as proto3 considers 0.0 (the default) the same as an unset value.
      dict(
          testcase_name="float_rtol_zero_to_near_zero",
          msg=TestMessage(float_value=0.0),
          msg_other=TestMessage(float_value=0.2),
          rtol=1.1,
          expected_error="""
\\+ float_value: 0.2
""",
      ),
      dict(
          testcase_name="float_rtol_near_zero_to_zero",
          msg=TestMessage(float_value=0.2),
          msg_other=TestMessage(float_value=0.0),
          rtol=1.1,
          expected_error="""
\\- float_value: 0.2
""",
      ),
      # An optional value has explicit presence and can therefore differentiate
      # between an unset value and a value set to 0.0.
      # Only actually not setting the optional float fails the comparison.
      dict(
          testcase_name="float_rtol_optional_not_set_to_near_zero",
          msg=TestMessage(),
          msg_other=TestMessage(optional_float_value=0.2),
          rtol=1.1,
          expected_error="""
\\+ optional_float_value: 0.2
""",
      ),
      dict(
          testcase_name="float_rtol_optional_near_zero_to_not_set",
          msg=TestMessage(optional_float_value=0.2),
          msg_other=TestMessage(),
          rtol=1.1,
          expected_error="""
\\- optional_float_value: 0.2
""",
      ),
      dict(
          testcase_name="float_diff_keeps_other_floats",
          msg=TestMessage(float_list=[4.0, 1.95, 2.05]),
          msg_other=TestMessage(float_list=[5.0, 2.0, 2.03]),
          rtol=0.1,
          expected_error=f"""
\\- float_list: 4.0
{mismatch_line_re}
\\+ float_list: 5.0
{mismatch_line_re}
  float_list: 2.0
  float_list: 2.03
""",
      ),
      dict(
          testcase_name="float_list_rtol_list1",
          msg=TestMessage(float_list=[4.0, 2.2, 2.0]),
          msg_other=TestMessage(float_list=[3.95, 1.95, 2.05]),
          rtol=0.1,
          expected_error=f"""
  float_list: 3.95
\\- float_list: 2.2
{mismatch_line_re}
\\+ float_list: 1.95
{mismatch_line_re}
  float_list: 2.05
""",
      ),
      dict(
          testcase_name="float_list_rtol_list2",
          msg=TestMessage(float_list=[1.95, 4.0, 2.05]),
          msg_other=TestMessage(float_list=[4.05, 2.0, 2.0]),
          rtol=0.1,
          expected_error=f"""
\\- float_list: 1.95
\\- float_list: 4.0
\\+ float_list: 4.05
{mismatch_line_re}
  float_list: 2.0
\\+ float_list: 2.0
""",
      ),
      dict(
          testcase_name="float_list_rtol_list1_more_elements",
          msg=TestMessage(float_list=[4.0, 2.0, 2.0]),
          msg_other=TestMessage(float_list=[4.05, 1.95, 2.05, 2.0]),
          rtol=0.1,
          expected_error="""
  float_list: 4.05
  float_list: 1.95
  float_list: 2.05
\\+ float_list: 2.0
""",
      ),
      dict(
          testcase_name="float_list_rtol_list2_more_elements",
          msg=TestMessage(float_list=[4.0, 1.95, 2.05]),
          msg_other=TestMessage(float_list=[4.05, 2.0, 2.0, 2.0]),
          rtol=0.1,
          expected_error="""
  float_list: 4.05
  float_list: 2.0
  float_list: 2.0
\\+ float_list: 2.0
""",
      ),
      dict(
          testcase_name="float_list_rtol_list3_more_elements",
          msg=TestMessage(float_list=[4.0, 2.0, 2.05]),
          msg_other=TestMessage(float_list=[4.05, 1.95, 2.0, 2.0]),
          rtol=0.1,
          expected_error="""
  float_list: 4.05
  float_list: 1.95
  float_list: 2.0
\\+ float_list: 2.0
""",
      ),
      dict(
          testcase_name="float_list_rtol_list1_less_elements",
          msg=TestMessage(float_list=[4.0, 2.0, 2.05, 2.0]),
          msg_other=TestMessage(float_list=[4.05, 1.95]),
          rtol=0.1,
          expected_error="""
  float_list: 4.05
  float_list: 1.95
\\- float_list: 2.05
\\- float_list: 2.0
""",
      ),
      dict(
          testcase_name="float_list_rtol_same_num_of_individual_numbers",
          msg=TestMessage(float_list=[4.0, 1.95, 2.05]),
          msg_other=TestMessage(float_list=[4.05, 2.0, 2.03, 2.0]),
          rtol=0.1,
          expected_error="""
  float_list: 4.05
  float_list: 2.0
  float_list: 2.03
\\+ float_list: 2.0
""",
      ),
      dict(
          testcase_name="message_list_different_order_rtol",
          msg=TestMessage(
              message_list=[
                  TestMessage(float_value=11.0),
                  TestMessage(float_value=1.0),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(float_value=0.95),
                  TestMessage(float_value=10.1),
              ]
          ),
          rtol=0.1,
          expected_error=f"""
  message_list {{
\\-   float_value: 11.0
{mismatch_line_re}
\\+   float_value: 0.95
{mismatch_line_re}
  }}
  message_list {{
\\-   float_value: 1.0
{mismatch_line_re}
\\+   float_value: 10.1
{mismatch_line_re}
  }}
""",
      ),
  )
  def test_assert_proto2_equal_fails_with_assert_msg(
      self,
      msg,
      msg_other,
      expected_error,
      ignored_fields=None,
      rtol=None,
  ):
    with self.assertRaisesRegex(AssertionError, expected_error):
      compare.assertProto2Equal(
          self, msg, msg_other, ignored_fields=ignored_fields, rtol=rtol
      )

  @parameterized.named_parameters(
      dict(
          testcase_name="basic",
          msg=TestMessage(int64_value=42),
          msg_haystack=TestMessage(int64_value=42, string_value="more"),
      ),
      dict(
          testcase_name="nested_message",
          msg=TestMessage(
              int64_value=42,
              message_value=TestMessage(string_value="foo"),
          ),
          msg_haystack=TestMessage(
              int64_value=42,
              string_value="more",
              message_value=TestMessage(int64_value=99, string_value="foo"),
          ),
      ),
      dict(
          testcase_name="complex_message_vs_empty",
          msg=TestMessage(),
          msg_haystack=TestMessage(
              int64_value=42,
              message_value=TestMessage(
                  string_value="foo", message_value=TestMessage(bool_value=True)
              ),
              optional_string_value="bar",
              bar="baz",
              enum_value=TestMessage.TEST_ENUM_2,
              bar_msg=TestMessage(uint32_value=77),
              message_list=[
                  TestMessage(float_value=1.0),
                  TestMessage(float_value=2.0),
                  TestMessage(double_value=3.0),
              ],
              string_int32_map={"foo": 1, "bar": 2},
          ),
      ),
      dict(
          testcase_name="complex_message",
          msg=TestMessage(
              int64_value=42,
              message_value=TestMessage(
                  string_value="foo", message_value=TestMessage(bool_value=True)
              ),
              optional_string_value="bar",
              bar="baz",
              enum_value=TestMessage.TEST_ENUM_2,
              bar_msg=TestMessage(uint32_value=77),
              message_list=[
                  TestMessage(float_value=1.0),
                  TestMessage(float_value=2.0),
                  TestMessage(double_value=3.0),
              ],
              string_int32_map={"foo": 1, "bar": 2},
          ),
          msg_haystack=TestMessage(
              int64_value=42,
              message_value=TestMessage(
                  string_value="foo",
                  message_value=TestMessage(
                      bool_value=True, string_value="more"
                  ),
              ),
              optional_string_value="bar",
              bar="baz",
              enum_value=TestMessage.TEST_ENUM_2,
              bar_msg=TestMessage(uint32_value=77),
              message_list=[
                  TestMessage(float_value=1.0),
                  TestMessage(string_value="something"),
                  TestMessage(float_value=2.0),
                  TestMessage(double_value=3.0),
                  TestMessage(string_value="more"),
              ],
              string_int32_map={"foo": 1, "bar": 2},
              string_value="more",
          ),
      ),
      dict(
          testcase_name="ignored_fields",
          msg=TestMessage(int64_value=42),
          msg_haystack=TestMessage(int64_value=99, string_value="more"),
          ignored_fields=["int64_value"],
      ),
      dict(
          testcase_name="nested_ignored_fields",
          msg=TestMessage(message_value=TestMessage(int64_value=42)),
          msg_haystack=TestMessage(
              message_value=TestMessage(int64_value=99, string_value="more")
          ),
          ignored_fields=["message_value.int64_value"],
      ),
      dict(
          testcase_name="map_ignored_fields",
          msg=TestMessage(string_int32_map={"foo": 42}),
          msg_haystack=TestMessage(
              string_int32_map={"bar": 42}, string_value="more"
          ),
          ignored_fields=["string_int32_map"],
      ),
      dict(
          testcase_name="repeated_ignored_fields",
          msg=TestMessage(message_list=[TestMessage(int64_value=42)]),
          msg_haystack=TestMessage(
              message_list=[
                  TestMessage(int64_value=99),
              ],
              string_value="more",
          ),
          ignored_fields=["message_list"],
      ),
      dict(
          testcase_name="in_repeated_ignored_fields",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=1),
                  TestMessage(int64_value=42),
              ]
          ),
          msg_haystack=TestMessage(
              message_list=[
                  TestMessage(int64_value=1),
                  TestMessage(int64_value=99, string_value="more"),
              ]
          ),
          ignored_fields=["message_list.int64_value"],
      ),
      dict(
          testcase_name="list_added_item",
          msg=TestMessage(int32_list=[1, 2, 4]),
          msg_haystack=TestMessage(int32_list=[1, 2, 3, 4]),
      ),
      dict(
          testcase_name="message_list_added_item",
          msg=TestMessage(
              message_list=[
                  TestMessage(int32_value=1),
                  TestMessage(int32_value=2),
                  TestMessage(int32_value=4),
              ]
          ),
          msg_haystack=TestMessage(
              message_list=[
                  TestMessage(int32_value=1),
                  TestMessage(int32_value=2),
                  TestMessage(int32_value=3),
                  TestMessage(int32_value=4),
              ]
          ),
      ),
      dict(
          testcase_name="message_subset_items",
          msg=TestMessage(
              message_value=TestMessage(int32_value=1),
          ),
          msg_haystack=TestMessage(
              message_value=TestMessage(int32_value=1, string_value="diffing"),
          ),
      ),
      dict(
          testcase_name="message_list_subset_items_ignored_fields",
          msg=TestMessage(
              message_list=[
                  TestMessage(int32_value=1),
                  TestMessage(int32_value=2),
              ]
          ),
          msg_haystack=TestMessage(
              message_list=[
                  TestMessage(int32_value=1, string_value="diffing"),
                  TestMessage(int32_value=2),
                  TestMessage(int32_value=3),
              ]
          ),
          ignored_fields=["message_list.string_value"],
      ),
      dict(
          testcase_name="nested_paths_shorter_ignore_path",
          msg=TestMessage(
              message_value=TestMessage(
                  message_value=TestMessage(
                      foo_msg=TestMessage(
                          message_value=TestMessage(int64_value=42)
                      )
                  )
              )
          ),
          msg_haystack=TestMessage(
              message_value=TestMessage(
                  message_value=TestMessage(
                      foo_msg=TestMessage(
                          message_value=TestMessage(int64_value=99)
                      )
                  ),
                  string_value="more",
              ),
              string_value="more",
          ),
          ignored_fields=["message_value.message_value"],
      ),
      dict(
          testcase_name="nested_paths_ignored_fields",
          msg=TestMessage(
              message_list=[
                  TestMessage(
                      message_value=TestMessage(
                          foo_msg=TestMessage(
                              message_value=TestMessage(int64_value=42)
                          )
                      )
                  ),
              ]
          ),
          msg_haystack=TestMessage(
              message_list=[
                  TestMessage(
                      message_value=TestMessage(
                          foo_msg=TestMessage(
                              message_value=TestMessage(int64_value=99)
                          )
                      )
                  ),
              ]
          ),
          ignored_fields=[
              "message_list.message_value.foo_msg.message_value.int64_value"
          ],
      ),
      dict(
          testcase_name="switched_oneof_ignored_fields",
          msg=TestMessage(
              message_value=TestMessage(
                  foo_msg=TestMessage(message_value=TestMessage(int64_value=42))
              )
          ),
          msg_haystack=TestMessage(
              message_value=TestMessage(
                  bar_msg=TestMessage(
                      message_value=TestMessage(int64_value=42)
                  ),
                  string_value="more",
              )
          ),
          ignored_fields=[
              "message_value.foo_msg",
              "message_value.bar_msg",
          ],
      ),
      dict(
          testcase_name="switched_oneof_added_in_repeated",
          msg=TestMessage(
              message_list=[
                  TestMessage(
                      message_value=TestMessage(
                          foo_msg=TestMessage(
                              message_value=TestMessage(int64_value=42)
                          )
                      )
                  ),
              ]
          ),
          msg_haystack=TestMessage(
              message_list=[
                  TestMessage(
                      message_value=TestMessage(
                          bar_msg=TestMessage(
                              message_value=TestMessage(int64_value=42)
                          )
                      )
                  ),
                  TestMessage(
                      message_value=TestMessage(
                          foo_msg=TestMessage(
                              message_value=TestMessage(int64_value=42)
                          )
                      )
                  ),
              ]
          ),
      ),
  )
  def test_assert_proto2_contains(self, msg, msg_haystack, ignored_fields=None):
    """Checks if fields in msg are also in msg_haystack."""
    compare.assertProto2Contains(
        self, msg, msg_haystack, ignored_fields=ignored_fields
    )

  @parameterized.named_parameters(
      dict(
          testcase_name="failed_compare",
          msg=TestMessage(int64_value=42),
          msg_haystack=TestMessage(int64_value=99),
          expected_error=f"""
\\- int64_value: 42
{mismatch_line_re}
\\+ int64_value: 99
{mismatch_line_re}
""",
      ),
      dict(
          testcase_name="extra_data",
          msg=TestMessage(int64_value=42),
          msg_haystack=TestMessage(),
          expected_error="""
\\- int64_value: 42
""",
      ),
      dict(
          testcase_name="nested_message_compare",
          msg=TestMessage(
              int64_value=42,
              message_value=TestMessage(string_value="foo", int64_value=99),
          ),
          msg_haystack=TestMessage(
              int64_value=42,
              message_value=TestMessage(string_value="bar"),
          ),
          expected_error=f"""
  int64_value: 42
  message_value {{
\\-   int64_value: 99
\\-   string_value: "foo"
{mismatch_line_re}
\\+   string_value: "bar"
{mismatch_line_re}
 *}}""",
      ),
      dict(
          testcase_name="nested_messages_multiple_missing",
          msg=TestMessage(
              int64_value=42,
              message_value=TestMessage(string_value="foo"),
          ),
          msg_haystack=TestMessage(
              message_value=TestMessage(),
          ),
          expected_error="""
\\- int64_value: 42
  message_value {
\\-   string_value: "foo"
  }""",
      ),
      dict(
          testcase_name="complex_message",
          msg=TestMessage(
              int64_value=42,
              message_value=TestMessage(
                  string_value="foo", message_value=TestMessage(bool_value=True)
              ),
              optional_string_value="bar",
              bar="baz",
              enum_value=TestMessage.TEST_ENUM_2,
              bar_msg=TestMessage(uint32_value=77),
              message_list=[
                  TestMessage(float_value=1.0),
                  TestMessage(float_value=2.0),
                  TestMessage(double_value=3.0),
              ],
              string_int32_map={"foo": 1, "bar": 2},
          ),
          msg_haystack=TestMessage(
              int64_value=42,
              message_value=TestMessage(
                  string_value="foo", message_value=TestMessage(bool_value=True)
              ),
              optional_string_value="bar",
              bar="baz",
              bar_msg=TestMessage(uint32_value=77),
              message_list=[
                  TestMessage(float_value=1.0),
                  TestMessage(float_value=2.6),
                  TestMessage(double_value=3.0),
              ],
              string_int32_map={"baz": 1, "bar": 3},
          ),
          expected_error=f"""(?s)
\\- enum_value: TEST_ENUM_2
{non_mismatch_lines}
\\-   float_value: 2.0
\\- }}
\\- message_list {{
{non_mismatch_lines}
  string_int32_map {{
    key: "bar"
\\-   value: 2
{mismatch_line_re}
\\+   value: 3
{mismatch_line_re}
  }}
{non_mismatch_lines}
\\- string_int32_map {{
\\-   key: "foo"
\\-   value: 1
\\- }}
{non_mismatch_lines}
""",
      ),
      dict(
          testcase_name="list_missing_item",
          msg=TestMessage(int32_list=[1, 2, 3, 4]),
          msg_haystack=TestMessage(int32_list=[1, 2, 4, 5]),
          expected_error="""
  int32_list: 1
  int32_list: 2
- int32_list: 3
  int32_list: 4
  int32_list: 5
""",
      ),
      dict(
          testcase_name="message_list_missing_item",
          msg=TestMessage(
              message_list=[
                  TestMessage(int32_value=1),
                  TestMessage(int32_value=2),
                  TestMessage(int32_value=3),
                  TestMessage(int32_value=4),
              ]
          ),
          msg_haystack=TestMessage(
              message_list=[
                  TestMessage(int32_value=1),
                  TestMessage(int32_value=2),
                  TestMessage(int32_value=4),
                  TestMessage(int32_value=5),
              ]
          ),
          expected_error=r"""
  message_list {
    int32_value: 1
  }
  message_list {
    int32_value: 2
  }
  message_list {
\-   int32_value: 3
\- }
\- message_list {
    int32_value: 4
  }
  message_list {
    int32_value: 5
  }
""",
      ),
      dict(
          testcase_name="message_list_diffing_item",
          msg=TestMessage(
              message_list=[
                  TestMessage(int32_value=1),
                  TestMessage(),
                  TestMessage(int32_value=3),
                  TestMessage(int32_value=4),
              ]
          ),
          msg_haystack=TestMessage(
              message_list=[
                  TestMessage(int32_value=1),
                  TestMessage(int32_value=2),
                  TestMessage(),
                  TestMessage(int32_value=4),
                  TestMessage(int32_value=5),
              ]
          ),
          expected_error=r"""
  message_list {
  }
  message_list {
    int32_value: 1
  }
  message_list {
    int32_value: 2
  }
  message_list {
\-   int32_value: 3
\- }
\- message_list {
    int32_value: 4
  }
  message_list {
    int32_value: 5
  }
""",
      ),
      dict(
          testcase_name="message_list_subset_items",
          msg=TestMessage(
              message_list=[
                  TestMessage(int32_value=1),
                  TestMessage(int32_value=2),
              ]
          ),
          msg_haystack=TestMessage(
              message_list=[
                  TestMessage(int32_value=1, string_value="diffing"),
                  TestMessage(int32_value=2),
              ]
          ),
          expected_error=r"""
\- message_list {
\-   int32_value: 1
\- }
""",
      ),
      dict(
          testcase_name="switched_oneof_ignored_one_oneof",
          msg=TestMessage(
              message_value=TestMessage(
                  message_value=TestMessage(
                      foo_msg=TestMessage(
                          message_value=TestMessage(int64_value=42)
                      )
                  )
              ),
          ),
          msg_haystack=TestMessage(
              message_value=TestMessage(
                  message_value=TestMessage(
                      bar_msg=TestMessage(
                          message_value=TestMessage(int64_value=42)
                      )
                  )
              ),
          ),
          ignored_fields=[
              "message_value.message_value.bar_msg",
          ],
          expected_error=r"""
  message_value {
    message_value {
-     foo_msg {
-       message_value {
-         int64_value: 42
-       }
-     }
    }
  }
""",
      ),
  )
  def test_assert_proto2_contains_fails_with_assert_msg(
      self, msg, msg_haystack, expected_error, ignored_fields=None
  ):
    with self.assertRaisesRegex(AssertionError, expected_error):
      compare.assertProto2Contains(
          self, msg, msg_haystack, ignored_fields=ignored_fields
      )

  @parameterized.named_parameters(
      dict(
          testcase_name="basic_list",
          msg=TestMessage(int32_list=[4, 2]),
          msg_other=TestMessage(int32_list=[4, 2]),
      ),
      dict(
          testcase_name="basic_list_different_order",
          msg=TestMessage(int32_list=[4, 2]),
          msg_other=TestMessage(int32_list=[2, 4]),
      ),
      dict(
          testcase_name="basic_list_different_count",
          msg=TestMessage(int32_list=[4, 2, 2]),
          msg_other=TestMessage(int32_list=[4, 2, 4, 4]),
      ),
      dict(
          testcase_name="basic_list_multiples_same_count",
          msg=TestMessage(int32_list=[4, 2, 4, 2]),
          msg_other=TestMessage(int32_list=[2, 2, 4, 4]),
          keep_duplicate_values=True,
      ),
      dict(
          testcase_name="float_list",
          msg=TestMessage(float_list=[4.0, 2.0]),
          msg_other=TestMessage(float_list=[4.0, 2.0]),
      ),
      dict(
          testcase_name="float_list_different_order",
          msg=TestMessage(float_list=[4.0, 2.0]),
          msg_other=TestMessage(float_list=[2.0, 4.0]),
      ),
      dict(
          testcase_name="float_list_different_count",
          msg=TestMessage(float_list=[4.0, 2.0, 2.0]),
          msg_other=TestMessage(float_list=[4.0, 2.0, 4.0, 2.0]),
      ),
      dict(
          testcase_name="float_list_multiples_same_count",
          msg=TestMessage(float_list=[4.0, 2.0, 4.0, 2.0]),
          msg_other=TestMessage(float_list=[4.0, 2.0, 2.0, 4.0]),
          keep_duplicate_values=True,
      ),
      dict(
          testcase_name="string_list",
          msg=TestMessage(string_list=["a", "b"]),
          msg_other=TestMessage(string_list=["a", "b"]),
      ),
      dict(
          testcase_name="string_list_different_order",
          msg=TestMessage(string_list=["b", "a"]),
          msg_other=TestMessage(string_list=["a", "b"]),
      ),
      dict(
          testcase_name="string_list_different_count",
          msg=TestMessage(string_list=["b", "a", "a"]),
          msg_other=TestMessage(string_list=["b", "a", "b", "b"]),
      ),
      dict(
          testcase_name="string_list_multiples_same_count",
          msg=TestMessage(string_list=["b", "a", "a", "b"]),
          msg_other=TestMessage(string_list=["b", "a", "b", "a"]),
          keep_duplicate_values=True,
      ),
      dict(
          testcase_name="message_list",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=2),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=2),
              ]
          ),
      ),
      dict(
          testcase_name="message_list_different_order",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=2),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=4),
              ]
          ),
      ),
      dict(
          testcase_name="message_list_different_count",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=2),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=4),
              ]
          ),
      ),
      dict(
          testcase_name="message_list_multiples_same_count",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=4),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=2),
              ]
          ),
          keep_duplicate_values=True,
      ),
      dict(
          testcase_name="multiple_list",
          msg=TestMessage(
              cord_list=["a", "b"],
              double_list=[1.0, 2.0],
              message_list=[
                  TestMessage(string_value="a"),
                  TestMessage(string_value="b"),
              ],
          ),
          msg_other=TestMessage(
              cord_list=["a", "b"],
              double_list=[1.0, 2.0],
              message_list=[
                  TestMessage(string_value="a"),
                  TestMessage(string_value="b"),
              ],
          ),
      ),
      dict(
          testcase_name="multiple_list_different_order",
          msg=TestMessage(
              cord_list=["a", "b"],
              double_list=[1.0, 2.0],
              message_list=[
                  TestMessage(string_value="a"),
                  TestMessage(string_value="b"),
              ],
          ),
          msg_other=TestMessage(
              cord_list=["b", "a"],
              double_list=[2.0, 1.0],
              message_list=[
                  TestMessage(string_value="b"),
                  TestMessage(string_value="a"),
              ],
          ),
      ),
      dict(
          testcase_name="multiple_list_different_count",
          msg=TestMessage(
              cord_list=["a", "b", "b"],
              double_list=[1.0, 2.0],
              message_list=[
                  TestMessage(string_value="a"),
                  TestMessage(string_value="b"),
                  TestMessage(string_value="b"),
                  TestMessage(string_value="b"),
                  TestMessage(string_value="b"),
              ],
          ),
          msg_other=TestMessage(
              cord_list=["a", "b", "a", "a"],
              double_list=[1.0, 2.0, 1.0, 1.0],
              message_list=[
                  TestMessage(string_value="a"),
                  TestMessage(string_value="a"),
                  TestMessage(string_value="b"),
              ],
          ),
      ),
      dict(
          testcase_name="multiple_list_multiple_same_count",
          msg=TestMessage(
              cord_list=["a", "b", "b", "a"],
              double_list=[1.0, 2.0, 1.0],
              message_list=[
                  TestMessage(string_value="a"),
                  TestMessage(string_value="b"),
                  TestMessage(string_value="b"),
                  TestMessage(string_value="a"),
                  TestMessage(string_value="a"),
              ],
          ),
          msg_other=TestMessage(
              cord_list=["a", "b", "a", "b"],
              double_list=[2.0, 1.0, 1.0],
              message_list=[
                  TestMessage(string_value="b"),
                  TestMessage(string_value="a"),
                  TestMessage(string_value="a"),
                  TestMessage(string_value="a"),
                  TestMessage(string_value="b"),
              ],
          ),
          keep_duplicate_values=True,
      ),
      dict(
          testcase_name="list_mixed_messages",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=1),
                  TestMessage(int64_value=1),
                  TestMessage(int64_value=2),
                  TestMessage(string_value="a"),
                  TestMessage(string_value="b"),
              ],
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=1),
                  TestMessage(string_value="a"),
                  TestMessage(string_value="b"),
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=2),
                  TestMessage(string_value="a"),
                  TestMessage(string_value="a"),
                  TestMessage(int64_value=2),
              ],
          ),
      ),
      dict(
          testcase_name="list_mixed_messages_multiple_same_count",
          msg=TestMessage(
              message_list=[
                  TestMessage(string_value="a"),
                  TestMessage(string_value="a"),
                  TestMessage(int64_value=1),
                  TestMessage(int64_value=1),
                  TestMessage(int64_value=2),
                  TestMessage(string_value="a"),
                  TestMessage(string_value="b"),
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=2),
              ],
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=1),
                  TestMessage(string_value="a"),
                  TestMessage(string_value="b"),
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=2),
                  TestMessage(string_value="a"),
                  TestMessage(int64_value=1),
                  TestMessage(string_value="a"),
                  TestMessage(int64_value=2),
              ],
          ),
          keep_duplicate_values=True,
      ),
      dict(
          testcase_name="nested_message",
          msg=TestMessage(
              int64_value=42,
              message_value=TestMessage(
                  string_value="foo", int32_list=[1, 1, 2, 2]
              ),
          ),
          msg_other=TestMessage(
              int64_value=42,
              message_value=TestMessage(string_value="foo", int32_list=[2, 1]),
          ),
      ),
      dict(
          testcase_name="in_nested_lists",
          msg=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(uint64_value=1),
                          TestMessage(uint64_value=2),
                          TestMessage(uint64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=2.0),
                          TestMessage(float_value=2.0),
                      ]
                  ),
              ],
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=1),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(uint64_value=1),
                          TestMessage(uint64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=2.0),
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=1.0),
                      ]
                  ),
              ],
          ),
      ),
      dict(
          testcase_name="in_nested_lists_multiple_same_elements",
          msg=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(uint64_value=1),
                          TestMessage(uint64_value=2),
                          TestMessage(uint64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=2.0),
                      ]
                  ),
              ],
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=1),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(uint64_value=2),
                          TestMessage(uint64_value=1),
                          TestMessage(uint64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=2.0),
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=1.0),
                      ]
                  ),
              ],
          ),
          keep_duplicate_values=True,
      ),
      dict(
          testcase_name="in_nested_lists_multiple_same_elements_nested",
          msg=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(uint64_value=1),
                          TestMessage(uint64_value=2),
                          TestMessage(uint64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=2.0),
                      ]
                  ),
              ],
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=1),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=2.0),
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=1.0),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(uint64_value=2),
                          TestMessage(uint64_value=1),
                          TestMessage(uint64_value=2),
                      ]
                  ),
              ],
          ),
          keep_duplicate_values=True,
      ),
      dict(
          testcase_name="nested_lists",
          msg=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(uint64_value=1),
                          TestMessage(uint64_value=2),
                          TestMessage(uint64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=2.0),
                      ]
                  ),
              ],
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(uint64_value=1),
                          TestMessage(uint64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=2.0),
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=1.0),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=1),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=1),
                      ]
                  ),
              ],
          ),
      ),
      dict(
          testcase_name="in_map",
          msg=TestMessage(
              string_message_map={
                  "foo": TestMessage(int64_list=[1, 2]),
                  "bar": TestMessage(
                      message_list=[
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=2),
                      ]
                  ),
              }
          ),
          msg_other=TestMessage(
              string_message_map={
                  "foo": TestMessage(int64_list=[2, 1, 2]),
                  "bar": TestMessage(
                      message_list=[
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=2),
                      ]
                  ),
              }
          ),
      ),
      dict(
          testcase_name="ignored_fields",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=1, string_value="a"),
                  TestMessage(int64_value=2, string_value="a"),
                  TestMessage(int64_value=3, string_value="b"),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int64_value=95, string_value="a"),
                  TestMessage(int64_value=96, string_value="b"),
                  TestMessage(int64_value=97, string_value="a"),
                  TestMessage(int64_value=98, string_value="a"),
                  TestMessage(int64_value=99, string_value="b"),
              ]
          ),
          ignored_fields=["message_list.int64_value"],
      ),
  )
  def test_assert_proto2_same_elements(
      self,
      msg,
      msg_other,
      ignored_fields=None,
      keep_duplicate_values=False,
  ):
    """Checks if msg has the same elements as msg_other - in any order."""
    compare.assertProto2SameElements(
        self,
        msg,
        msg_other,
        ignored_fields=ignored_fields,
        keep_duplicate_values=keep_duplicate_values,
    )

  @parameterized.named_parameters(
      dict(
          testcase_name="failed_compare",
          msg=TestMessage(int64_value=42),
          msg_other=TestMessage(int64_value=99),
          expected_error=f"""
\\- int64_value: 42
{mismatch_line_re}
\\+ int64_value: 99
{mismatch_line_re}
""",
      ),
      dict(
          testcase_name="extra_data",
          msg=TestMessage(int64_list=[4, 2]),
          msg_other=TestMessage(int64_list=[2, 4, 3, 2]),
          expected_error="""
\\+ int64_list: 3
""",
      ),
      dict(
          testcase_name="missing_data",
          msg=TestMessage(int64_list=[4, 3, 2]),
          msg_other=TestMessage(int64_list=[2, 4, 2]),
          expected_error="""
\\- int64_list: 3
""",
      ),
      dict(
          testcase_name="extra_and_missing_data",
          msg=TestMessage(int64_list=[3, 3, 2]),
          msg_other=TestMessage(int64_list=[3, 4, 4]),
          expected_error=f"""
\\- int64_list: 2
{non_mismatch_lines}
\\+ int64_list: 4
""",
      ),
      dict(
          testcase_name="extra_message_data",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=2),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=3),
                  TestMessage(int64_value=2),
              ]
          ),
          expected_error="""
\\+   int64_value: 3
\\+ }
\\+ message_list {
""",
      ),
      dict(
          testcase_name="missing_message_data",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=3),
                  TestMessage(int64_value=2),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=2),
              ]
          ),
          expected_error="""
\\-   int64_value: 3
\\- }
\\- message_list {
""",
      ),
      dict(
          testcase_name="extra_and_missing_message_data",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=3),
                  TestMessage(int64_value=3),
                  TestMessage(int64_value=2),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int64_value=3),
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=4),
              ]
          ),
          expected_error=f"""
\\- message_list {{
\\-   int64_value: 2
\\- }}
{non_mismatch_lines}
\\+ message_list {{
\\+   int64_value: 4
\\+ }}
""",
      ),
      dict(
          testcase_name="extra_message_data_mixed_msgs",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=4),
                  TestMessage(string_value="a"),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(string_value="a"),
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=3),
                  TestMessage(string_value="a"),
              ]
          ),
          expected_error="""
\\+ message_list {
\\+   int64_value: 3
\\+ }
""",
      ),
      dict(
          testcase_name="missing_message_data_mixed_msgs",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=3),
                  TestMessage(string_value="a"),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(string_value="a"),
                  TestMessage(int64_value=4),
                  TestMessage(string_value="a"),
              ]
          ),
          expected_error="""
\\- message_list {
\\-   int64_value: 3
\\- }
""",
      ),
      dict(
          testcase_name="extra_and_missing_message_data_mixed_msgs",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=3),
                  TestMessage(int64_value=3),
                  TestMessage(string_value="a"),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int64_value=3),
                  TestMessage(bool_value=True),
                  TestMessage(bool_value=True),
              ]
          ),
          expected_error=f"""
\\+ message_list {{
\\+   bool_value: true
\\+ }}
{non_mismatch_lines}
\\- message_list {{
\\-   string_value: "a"
\\- }}
""",
      ),
      dict(
          testcase_name="extra_message_data_mixed_data_in_msgs",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=4),
                  TestMessage(string_value="a"),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(string_value="a"),
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=4, string_value="a"),
                  TestMessage(string_value="a"),
              ]
          ),
          expected_error="""(?s)
\\+   int64_value: 4
.*
\\+ message_list {
\\+   string_value: "a"
\\+ }
""",
      ),
      dict(
          testcase_name="missing_message_data_mixed_data_in_msgs",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=4, string_value="a"),
                  TestMessage(string_value="a"),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(string_value="a"),
                  TestMessage(int64_value=4),
                  TestMessage(string_value="a"),
              ]
          ),
          expected_error="""(?s)
\\-   int64_value: 4
.*
\\- message_list {
\\-   string_value: "a"
\\- }
""",
      ),
      dict(
          testcase_name="extra_and_missing_message_data_mixed_data_in_msgs",
          msg=TestMessage(
              message_list=[
                  TestMessage(string_value="b"),
                  TestMessage(int64_value=4, string_value="b"),
                  TestMessage(int64_value=4),
                  TestMessage(string_value="a"),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(string_value="a"),
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=4, string_value="a"),
                  TestMessage(string_value="a"),
                  TestMessage(string_value="b"),
              ]
          ),
          expected_error=f"""(?s)
  message_list {{
    int64_value: 4
\\-   string_value: "b"
{mismatch_line_re}
\\+   string_value: "a"
{mismatch_line_re}
  }}
""",
      ),
      dict(
          testcase_name="basic_list_different_individual_count",
          msg=TestMessage(int32_list=[4, 2, 2, 4]),
          msg_other=TestMessage(int32_list=[4, 2, 4, 4]),
          keep_duplicate_values=True,
          expected_error=f"""(?s)
\\- int32_list: 2
{non_mismatch_lines}
\\+ int32_list: 4
""",
      ),
      dict(
          testcase_name="float_list_different_individual_count",
          msg=TestMessage(float_list=[4.0, 2.0, 2.0, 2.0]),
          msg_other=TestMessage(float_list=[4.0, 2.0, 4.0, 4.0]),
          keep_duplicate_values=True,
          expected_error=f"""(?s)
\\- float_list: 2.0
\\- float_list: 2.0
{non_mismatch_lines}
\\+ float_list: 4.0
\\+ float_list: 4.0
""",
      ),
      dict(
          testcase_name="string_list_different_individual_count",
          msg=TestMessage(string_list=["b", "a", "a", "a"]),
          msg_other=TestMessage(string_list=["b", "a", "b", "a"]),
          keep_duplicate_values=True,
          expected_error=f"""(?s)
\\- string_list: "a"
{non_mismatch_lines}
\\+ string_list: "b"
""",
      ),
      dict(
          testcase_name="message_list_different_individual_count",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=2),
              ]
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int64_value=4),
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=4),
              ]
          ),
          keep_duplicate_values=True,
          expected_error=f"""(?s)
\\- message_list {{
\\-   int64_value: 2
\\- }}
{non_mismatch_lines}
\\+ message_list {{
\\+   int64_value: 4
\\+ }}
""",
      ),
      dict(
          testcase_name="multiple_list_different_individual_count",
          msg=TestMessage(
              cord_list=["a", "b", "b"],
              double_list=[1.0, 2.0, 1.0, 2.0],
              message_list=[
                  TestMessage(string_value="a"),
                  TestMessage(string_value="b"),
                  TestMessage(string_value="b"),
                  TestMessage(string_value="b"),
                  TestMessage(string_value="b"),
              ],
          ),
          msg_other=TestMessage(
              cord_list=["a", "b", "a"],
              double_list=[1.0, 2.0, 1.0, 1.0],
              message_list=[
                  TestMessage(string_value="a"),
                  TestMessage(string_value="a"),
                  TestMessage(string_value="b"),
              ],
          ),
          keep_duplicate_values=True,
          expected_error=f"""(?s)
\\+ double_list: 1.0
{non_mismatch_lines}
\\- double_list: 2.0
\\+ cord_list: "a"
{non_mismatch_lines}
\\- cord_list: "b"
\\+ message_list {{
\\+   string_value: "a"
\\+ }}
{non_mismatch_lines}
\\- message_list {{
\\-   string_value: "b"
\\- }}
\\- message_list {{
\\-   string_value: "b"
\\- }}
\\- message_list {{
\\-   string_value: "b"
\\- }}
""",
      ),
      dict(
          testcase_name="list_mixed_messages_different_individual_count",
          msg=TestMessage(
              message_list=[
                  TestMessage(int64_value=1),
                  TestMessage(int64_value=1),
                  TestMessage(int64_value=2),
                  TestMessage(string_value="a"),
                  TestMessage(string_value="b"),
              ],
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=1),
                  TestMessage(string_value="a"),
                  TestMessage(string_value="b"),
                  TestMessage(int64_value=2),
                  TestMessage(int64_value=2),
                  TestMessage(string_value="a"),
                  TestMessage(string_value="a"),
                  TestMessage(int64_value=2),
              ],
          ),
          keep_duplicate_values=True,
          expected_error=f"""(?s)
  message_list {{
\\-   int64_value: 1
{mismatch_line_re}
\\+   int64_value: 2
{mismatch_line_re}
\\+ }}
\\+ message_list {{
\\+   int64_value: 2
\\+ }}
\\+ message_list {{
\\+   int64_value: 2
{non_mismatch_lines}
\\+   string_value: "a"
\\+ }}
\\+ message_list {{
\\+   string_value: "a"
\\+ }}
\\+ message_list {{
""",
      ),
      dict(
          testcase_name="in_nested_lists_different_individual_count",
          msg=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(uint64_value=1),
                          TestMessage(uint64_value=2),
                          TestMessage(uint64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=2.0),
                          TestMessage(float_value=2.0),
                      ]
                  ),
              ],
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=1),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(uint64_value=1),
                          TestMessage(uint64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=2.0),
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=1.0),
                      ]
                  ),
              ],
          ),
          keep_duplicate_values=True,
          expected_error=f"""(?s)
  message_list {{
{non_mismatch_lines}
\\-   message_list {{
\\-     float_value: 2.0
\\-   }}
  }}
  message_list {{
\\-   message_list {{
\\-     int64_value: 1
\\-   }}
{non_mismatch_lines}
  }}
  message_list {{
{non_mismatch_lines}
\\-   message_list {{
\\-     uint64_value: 2
\\-   }}
  }}
""",
      ),
      dict(
          testcase_name=(
              "nested_lists_different_count_with_nested_same_elements"
          ),
          msg=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(uint64_value=1),
                          TestMessage(uint64_value=2),
                          TestMessage(uint64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=2.0),
                      ]
                  ),
              ],
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(uint64_value=1),
                          TestMessage(uint64_value=2),
                          TestMessage(uint64_value=1),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=2.0),
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=1.0),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=1),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=1),
                      ]
                  ),
              ],
          ),
          keep_duplicate_values=True,
          expected_error=f"""(?s)
\\+     int64_value: 1
\\+   }}
\\+   message_list {{
\\+     int64_value: 2
\\+   }}
\\+   message_list {{
\\+     int64_value: 2
\\+   }}
\\+ }}
\\+ message_list {{
\\+   message_list {{
\\+     uint64_value: 1
\\+   }}
\\+   message_list {{
{non_mismatch_lines}
\\-   message_list {{
\\-     uint64_value: 2
\\-   }}
  }}
""",
      ),
      dict(
          testcase_name="nested_lists_multiple_same_elements",
          msg=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(uint64_value=1),
                          TestMessage(uint64_value=2),
                          TestMessage(uint64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=2.0),
                      ]
                  ),
              ],
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(uint64_value=1),
                          TestMessage(uint64_value=2),
                          TestMessage(uint64_value=1),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=2.0),
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=1.0),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=1),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=1),
                      ]
                  ),
              ],
          ),
          keep_duplicate_values=True,
          expected_error=f"""(?s)
\\+     int64_value: 1
\\+   }}
\\+   message_list {{
\\+     int64_value: 2
\\+   }}
\\+   message_list {{
\\+     int64_value: 2
\\+   }}
\\+ }}
\\+ message_list {{
\\+   message_list {{
\\+     uint64_value: 1
\\+   }}
\\+   message_list {{
{non_mismatch_lines}
\\-   message_list {{
\\-     uint64_value: 2
\\-   }}
""",
      ),
      dict(
          testcase_name="nested_lists_different_individual_elements",
          msg=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=1),
                          TestMessage(int64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(uint64_value=1),
                          TestMessage(uint64_value=2),
                          TestMessage(uint64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=2.0),
                      ]
                  ),
              ],
          ),
          msg_other=TestMessage(
              message_list=[
                  TestMessage(
                      message_list=[
                          TestMessage(uint64_value=1),
                          TestMessage(uint64_value=2),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(float_value=2.0),
                          TestMessage(float_value=1.0),
                          TestMessage(float_value=1.0),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=1),
                      ]
                  ),
                  TestMessage(
                      message_list=[
                          TestMessage(int64_value=2),
                          TestMessage(int64_value=1),
                      ]
                  ),
              ],
          ),
          keep_duplicate_values=True,
          expected_error=f"""(?s)
  message_list {{
    message_list {{
      int64_value: 1
    }}
    message_list {{
\\+     int64_value: 2
\\+   }}
\\+ }}
\\+ message_list {{
\\+   message_list {{
      int64_value: 1
\\+   }}
\\+   message_list {{
\\+     int64_value: 2
    }}
    message_list {{
      int64_value: 2
    }}
  }}
{non_mismatch_lines}
\\-   message_list {{
\\-     uint64_value: 2
\\-   }}
""",
      ),
  )
  def test_assert_proto2_same_elements_fails_with_assert_msg(
      self,
      msg,
      msg_other,
      expected_error,
      ignored_fields=None,
      keep_duplicate_values=False,
  ):
    """Verifies failure for messages that contain different sets of fields."""
    with self.assertRaisesRegex(AssertionError, expected_error):
      compare.assertProto2SameElements(
          self,
          msg,
          msg_other,
          ignored_fields=ignored_fields,
          keep_duplicate_values=keep_duplicate_values,
      )


if __name__ == "__main__":
  absltest.main()
