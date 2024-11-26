# Copyright 2023 Intrinsic Innovation LLC

"""Provides behavior trees from a solution."""

from typing import Iterator
import grpc
from intrinsic.executive.proto import behavior_tree_pb2
from intrinsic.frontend.solution_service.proto import solution_service_pb2
from intrinsic.frontend.solution_service.proto import solution_service_pb2_grpc
from intrinsic.solutions import behavior_tree
from intrinsic.solutions import providers


_DEFAULT_PAGE_SIZE = 50


class BehaviorTrees(providers.BehaviorTreeProvider):
  """Provides behavior trees from a solution."""

  _solution: solution_service_pb2_grpc.SolutionServiceStub

  def __init__(self, solution: solution_service_pb2_grpc.SolutionServiceStub):
    self._solution = solution

  def _list_all_behavior_trees(self) -> list[behavior_tree_pb2.BehaviorTree]:
    response = self._solution.ListBehaviorTrees(
        solution_service_pb2.ListBehaviorTreesRequest(
            page_size=_DEFAULT_PAGE_SIZE
        )
    )
    bts = []
    bts.extend(response.behavior_trees)
    while response.next_page_token:
      response = self._solution.ListBehaviorTrees(
          solution_service_pb2.ListBehaviorTreesRequest(
              page_size=_DEFAULT_PAGE_SIZE,
              page_token=response.next_page_token,
          )
      )
      bts.extend(response.behavior_trees)
    return bts

  def keys(self) -> list[str]:
    """Returns the names of available behavior trees."""
    return [bt.name for bt in self._list_all_behavior_trees()]

  def __iter__(self) -> Iterator[str]:
    """Returns an iterator over the names of available behavior trees."""
    for bt in self._list_all_behavior_trees():
      yield bt.name

  def items(self) -> Iterator[tuple[str, behavior_tree.BehaviorTree]]:
    """Returns an iterator over the names and behavior trees."""
    for bt in self._list_all_behavior_trees():
      yield bt.name, behavior_tree.BehaviorTree(bt=bt)

  def values(self) -> Iterator[behavior_tree.BehaviorTree]:
    """Returns an iterator over the names and behavior trees."""
    for bt in self._list_all_behavior_trees():
      yield behavior_tree.BehaviorTree(bt=bt)

  def __contains__(self, name: str) -> bool:
    """Returns whether the behavior tree with the given name is available.

    Args:
      name: The name of the behavior tree.
    """
    try:
      self._solution.GetBehaviorTree(
          solution_service_pb2.GetBehaviorTreeRequest(name=name)
      )
      return True
    except grpc.RpcError as e:
      if hasattr(e, 'code') and e.code() == grpc.StatusCode.NOT_FOUND:
        return False
      raise e

  def __getitem__(self, name: str) -> behavior_tree.BehaviorTree:
    """Returns the behavior tree with the given behavior tree id.

    Args:
      name: The name of the behavior tree.
    """
    try:
      return behavior_tree.BehaviorTree(
          bt=self._solution.GetBehaviorTree(
              solution_service_pb2.GetBehaviorTreeRequest(name=name)
          )
      )
    except Exception as e:
      raise KeyError(f'Behavior tree "{name}" not available') from e

  def __setitem__(self, name: str, value: behavior_tree.BehaviorTree):
    """Updates the behavior tree with the given name in the solution.

    Args:
      name: The name to assign the behavior tree.
      value: The behavior tree to set.
    """
    value.name = name
    self._solution.UpdateBehaviorTree(
        solution_service_pb2.UpdateBehaviorTreeRequest(
            behavior_tree=value.proto,
            allow_missing=True,
        )
    )

  def __delitem__(self, name: str):
    """Deletes the behavior tree with the given name from the solution."""
    try:
      self._solution.DeleteBehaviorTree(
          solution_service_pb2.DeleteBehaviorTreeRequest(name=name)
      )
    except Exception as e:
      raise KeyError(f"Failed to delete behavior tree '{name}'") from e
