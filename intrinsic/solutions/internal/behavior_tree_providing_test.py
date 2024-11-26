# Copyright 2023 Intrinsic Innovation LLC

"""Tests of behavior_tree_providing.py."""

from unittest import mock

from absl.testing import absltest
import grpc
from intrinsic.executive.proto import behavior_tree_pb2
from intrinsic.frontend.solution_service.proto import solution_service_pb2
from intrinsic.solutions import behavior_tree
from intrinsic.solutions.internal import behavior_tree_providing


def _behavior_tree_with_name(name: str):
  bt = behavior_tree_pb2.BehaviorTree()
  bt.name = name
  bt.root.task.call_behavior.skill_id = "ai.intrinsic.skill-0"
  bt.root.name = "ai.intrinsic.skill-0"
  bt.root.id = 1
  bt.root.state = behavior_tree_pb2.BehaviorTree.State.ACCEPTED
  return bt


class BehaviorTreeProvidingTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self._solution_service = mock.MagicMock()
    self._behavior_trees = behavior_tree_providing.BehaviorTrees(
        self._solution_service
    )

  def test_keys_empty(self):
    self._solution_service.ListBehaviorTrees.return_value = (
        solution_service_pb2.ListBehaviorTreesResponse(
            behavior_trees=None,
            next_page_token=None,
        )
    )

    self.assertEqual(self._behavior_trees.keys(), [])

  def test_keys_single_page(self):
    self._solution_service.ListBehaviorTrees.return_value = (
        solution_service_pb2.ListBehaviorTreesResponse(
            behavior_trees=[
                _behavior_tree_with_name("tree1"),
                _behavior_tree_with_name("tree2"),
            ],
            next_page_token=None,
        )
    )

    self.assertEqual(self._behavior_trees.keys(), ["tree1", "tree2"])

  def test_keys_multiple_pages(self):
    self._solution_service.ListBehaviorTrees.side_effect = (
        solution_service_pb2.ListBehaviorTreesResponse(
            behavior_trees=[
                _behavior_tree_with_name("tree1"),
                _behavior_tree_with_name("tree2"),
            ],
            next_page_token="some_token",
        ),
        solution_service_pb2.ListBehaviorTreesResponse(
            behavior_trees=[
                _behavior_tree_with_name("tree3"),
            ],
            next_page_token=None,
        ),
    )

    self.assertEqual(self._behavior_trees.keys(), ["tree1", "tree2", "tree3"])
    self.assertSequenceEqual(
        self._solution_service.ListBehaviorTrees.mock_calls,
        (
            mock.call(
                solution_service_pb2.ListBehaviorTreesRequest(
                    page_size=behavior_tree_providing._DEFAULT_PAGE_SIZE,
                )
            ),
            mock.call(
                solution_service_pb2.ListBehaviorTreesRequest(
                    page_size=behavior_tree_providing._DEFAULT_PAGE_SIZE,
                    page_token="some_token",
                )
            ),
        ),
    )

  def test_iter(self):
    self._solution_service.ListBehaviorTrees.return_value = (
        solution_service_pb2.ListBehaviorTreesResponse(
            behavior_trees=[
                _behavior_tree_with_name("tree1"),
                _behavior_tree_with_name("tree2"),
            ],
            next_page_token=None,
        )
    )

    self.assertEqual(list(self._behavior_trees), ["tree1", "tree2"])

  def test_items(self):
    proto1 = _behavior_tree_with_name("tree1")
    proto2 = _behavior_tree_with_name("tree2")
    self._solution_service.ListBehaviorTrees.return_value = (
        solution_service_pb2.ListBehaviorTreesResponse(
            behavior_trees=[proto1, proto2],
            next_page_token=None,
        )
    )

    self.assertEqual(
        [(name, bt.proto) for name, bt in self._behavior_trees.items()],
        [("tree1", proto1), ("tree2", proto2)],
    )

  def test_values(self):
    proto1 = _behavior_tree_with_name("tree1")
    proto2 = _behavior_tree_with_name("tree2")
    self._solution_service.ListBehaviorTrees.return_value = (
        solution_service_pb2.ListBehaviorTreesResponse(
            behavior_trees=[proto1, proto2],
            next_page_token=None,
        )
    )

    self.assertEqual(
        [bt.proto for bt in self._behavior_trees.values()],
        [proto1, proto2],
    )

  def test_contains(self):
    def mock_get_behavior_tree(
        request: solution_service_pb2.GetBehaviorTreeRequest,
    ):
      if request.name == "tree1":
        return _behavior_tree_with_name("tree1")
      else:
        error = grpc.RpcError(request.name + " not found")
        error.code = lambda: grpc.StatusCode.NOT_FOUND
        raise error

    self._solution_service.GetBehaviorTree.side_effect = mock_get_behavior_tree

    self.assertIn("tree1", self._behavior_trees)
    self.assertNotIn("non_existent_tree", self._behavior_trees)

  def test_getitem(self):
    def mock_get_behavior_tree(
        request: solution_service_pb2.GetBehaviorTreeRequest,
    ):
      if request.name == "tree1":
        return _behavior_tree_with_name("tree1")
      else:
        error = grpc.RpcError(request.name + " not found")
        error.code = lambda: grpc.StatusCode.NOT_FOUND
        raise error

    self._solution_service.GetBehaviorTree.side_effect = mock_get_behavior_tree

    self.assertEqual(self._behavior_trees["tree1"].name, "tree1")
    with self.assertRaises(KeyError):
      self._behavior_trees["non_existent_tree"]  # pylint: disable=pointless-statement

  def test_setitem(self):
    bt = behavior_tree.BehaviorTree("tree1", root=behavior_tree.Fail("Failure"))

    self._behavior_trees["tree1"] = bt

    self._solution_service.UpdateBehaviorTree.assert_called_once_with(
        solution_service_pb2.UpdateBehaviorTreeRequest(
            behavior_tree=bt.proto,
            allow_missing=True,
        )
    )

  def test_delitem(self):
    del self._behavior_trees["tree1"]

    self._solution_service.DeleteBehaviorTree.assert_called_once_with(
        solution_service_pb2.DeleteBehaviorTreeRequest(name="tree1")
    )


if __name__ == "__main__":
  absltest.main()
