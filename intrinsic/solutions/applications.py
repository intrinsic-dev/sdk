# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Provides an API to the PPR application documents."""

from typing import Any, Dict, List

import grpc
from intrinsic.executive.app_edit_service.proto.public import app_edit_service_pb2
from intrinsic.executive.app_edit_service.proto.public import app_edit_service_pb2_grpc
from intrinsic.solutions import behavior_tree
from intrinsic.solutions import deployments
from intrinsic.solutions import ppr
from intrinsic.solutions import providers
from intrinsic.util.grpc import error_handling


DEFAULT_VOLUME = 'cloud'


class Application:
  """Provides access to the application PPR documents.

  Application is a Python client for the application data service. It provides
  access to the cluster/application/process/product catalogs.

  Attributes:
    product_parts: The ProductParts belonging to the running application.
  """

  def __init__(
      self,
      app_edit_stub: app_edit_service_pb2_grpc.AppEditServiceStub,
  ):
    """Creates an Application.

    Arguments:
      app_edit_stub: The AppEditStub.
    """
    self._app_edit_stub: app_edit_service_pb2_grpc.AppEditServiceStub = (
        app_edit_stub
    )

  class ProductParts:
    """Manages product parts of a product.

    ProductParts has the named ProductParts as attributes which are created
    after the creation.

    Attributes: 'product_part_name': A ProductPart.
    """

    def __init__(self, products: Dict[str, ppr.ProductPart]):
      for product_name, product in products.items():
        setattr(self, product_name, product)

  @error_handling.retry_on_grpc_unavailable
  def _call_get_current_product_parts(self) -> List[str]:
    return [
        p.product_part_name
        for p in self._app_edit_stub.GetCurrentProductParts(
            app_edit_service_pb2.GetCurrentProductPartsRequest()
        ).parts
    ]

  def get_product_part(self, name: str) -> ppr.ProductPart:
    product_parts = self._call_get_current_product_parts()
    if name not in product_parts:
      raise ValueError(
          'The running application does not have a product part with name: '
          f'{name}.'
      )
    return ppr.ProductPart(name)

  @property
  def product_parts(self) -> ProductParts:
    """Gets the product parts."""
    product_parts = self._call_get_current_product_parts()
    return Application.ProductParts(
        {name: ppr.ProductPart(name) for name in product_parts}
    )

  @error_handling.retry_on_grpc_unavailable
  def fetch_process_notebooks(self) -> Dict[str, str]:
    res = self._app_edit_stub.FetchProcessNotebooks(
        app_edit_service_pb2.FetchProcessNotebooksRequest()
    )
    return res.notebooks

  @error_handling.retry_on_grpc_unavailable
  def save_process_notebooks(self, notebooks: Dict[str, str]) -> None:
    req = app_edit_service_pb2.SaveProcessNotebooksRequest(notebooks=notebooks)
    self._app_edit_stub.SaveProcessNotebooks(req)

  @error_handling.retry_on_grpc_unavailable
  def fetch_process_behavior_trees(
      self,
  ) -> Dict[str, behavior_tree.BehaviorTree]:
    res = self._app_edit_stub.FetchProcessBehaviorTrees(
        app_edit_service_pb2.FetchProcessBehaviorTreesRequest()
    )
    return {
        name: behavior_tree.BehaviorTree.create_from_proto(tree)
        for name, tree in res.trees.items()
    }

  @error_handling.retry_on_grpc_unavailable
  def fetch_process_behavior_trees_names(
      self,
  ) -> List[str]:
    res = self._app_edit_stub.FetchProcessBehaviorTrees(
        app_edit_service_pb2.FetchProcessBehaviorTreesRequest()
    )
    return [k for (k, _) in res.trees.items()]

  @error_handling.retry_on_grpc_unavailable
  def print_python_for_process_behavior_tree(
      self, name: str, skills: providers.SkillProvider
  ) -> None:
    trees = self.fetch_process_behavior_trees()
    if name not in trees:
      raise KeyError('BehaviorTree with name ' + name + ' not found.')
    trees[name].print_python_code(skills)

  @error_handling.retry_on_grpc_unavailable
  def add_behavior_trees_to_process(self, trees: Dict[str, Any]) -> None:
    req = app_edit_service_pb2.AddBehaviorTreesToProcessRequest(trees=trees)
    self._app_edit_stub.AddBehaviorTreesToProcess(req)

  @error_handling.retry_on_grpc_unavailable
  def set_default_runnable(self, default_name: str, autostart: bool) -> None:
    req = app_edit_service_pb2.SetDefaultRunnableToCurrentProcessRequest(
        autostart=autostart, runnable_key=default_name
    )
    self._app_edit_stub.SetDefaultRunnableToCurrentProcess(req)

  @error_handling.retry_on_grpc_unavailable
  def set_process_data_file(self, content: bytes, path: str) -> None:
    self._app_edit_stub.SetProcessDataFile(
        app_edit_service_pb2.SetProcessDataFileRequest(
            content=content, path=path
        )
    )

  @error_handling.retry_on_grpc_unavailable
  def delete_process_data_file(self, path: str) -> None:
    self._app_edit_stub.DeleteProcessDataFile(
        app_edit_service_pb2.DeleteProcessDataFileRequest(path=path)
    )

  @error_handling.retry_on_grpc_unavailable
  def rename_process_data_file(self, old_path: str, new_path: str) -> None:
    self._app_edit_stub.RenameProcessDataFile(
        app_edit_service_pb2.RenameProcessDataFileRequest(
            old_path=old_path, new_path=new_path
        )
    )

  @classmethod
  def for_solution(cls, solution: deployments.Solution) -> 'Application':
    """Creates an Application instance for the given solution."""
    return cls(
        app_edit_service_pb2_grpc.AppEditServiceStub(solution.grpc_channel)
    )

  @classmethod
  def for_channel(cls, grpc_channel: grpc.Channel) -> 'Application':
    """Creates an Application connected via the given gRPC channel."""
    return cls(app_edit_service_pb2_grpc.AppEditServiceStub(grpc_channel))
