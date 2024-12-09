# Copyright 2023 Intrinsic Innovation LLC

"""Defines the GraspAnnotatorClient class."""

from typing import Tuple
from absl import logging
import grpc
from intrinsic.manipulation.grasping import grasp_annotations_pb2
from intrinsic.manipulation.service import grasp_annotator_service_pb2
from intrinsic.manipulation.service import grasp_annotator_service_pb2_grpc

DEFAULT_GRASP_ANNOTATOR_SERVICE_ADDRESS = (
    "istio-ingressgateway.app-ingress.svc.cluster.local:80"
)
DEFAULT_GRASP_ANNOTATOR_SERVICE_INSTANCE_NAME = "grasp_annotator_service"


class GraspAnnotatorClient:
  """Helper class for calling the rpcs in the GraspAnnotatorService."""

  def __init__(
      self,
      stub: grasp_annotator_service_pb2_grpc.GraspAnnotatorStub,
      instance_name: str = DEFAULT_GRASP_ANNOTATOR_SERVICE_INSTANCE_NAME,
  ):
    """Constructor.

    Args:
      stub: The GraspannotatorService stub.
      instance_name: The service instance name of the grasp annotator service.
        This is the name defined in `intrinsic_resource_instance`.
    """
    self._stub: grasp_annotator_service_pb2_grpc.GraspAnnotatorStub = stub
    self._connection_params = {
        "metadata": [(
            "x-resource-instance-name",
            instance_name,
        )]
    }

  @classmethod
  def connect(
      cls,
      address: str = DEFAULT_GRASP_ANNOTATOR_SERVICE_ADDRESS,
      instance_name: str = DEFAULT_GRASP_ANNOTATOR_SERVICE_INSTANCE_NAME,
  ) -> Tuple[grpc.Channel, "GraspAnnotatorClient"]:
    """Connects to the grasp annotator service.

    Args:
      address: The address of the grasp annotator service.
      instance_name: The service instance name of the grasp annotator service.
        This is the name defined in `intrinsic_resource_instance`.

    Returns:
      gRpc channel, grasp annotator client
    """
    logging.info("Connecting to grasp_annotator_service at %s", address)
    channel = grpc.insecure_channel(address)
    return channel, GraspAnnotatorClient(
        stub=grasp_annotator_service_pb2_grpc.GraspAnnotatorStub(channel),
        instance_name=instance_name,
    )

  def annotate_grasps(
      self,
      grasp_annotator_request: grasp_annotator_service_pb2.GraspAnnotatorRequest,
  ) -> grasp_annotations_pb2.GraspAnnotations:
    """Annotates grasps.

    Args:
      grasp_annotator_request: The parameters used to annotate grasps.

    Returns:
      The annotated grasps.
    """
    annotations = self._stub.Annotate(
        grasp_annotator_request,
        **self._connection_params,
    )
    return annotations
