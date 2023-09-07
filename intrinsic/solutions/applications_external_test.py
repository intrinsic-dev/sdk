# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""External smoke tests for applications."""
from unittest import mock

from absl.testing import absltest
from intrinsic.executive.app_edit_service.proto.public import app_edit_service_pb2
from intrinsic.solutions import applications


class ApplicationClientExternalTest(absltest.TestCase):

  def setUp(self):
    super().setUp()

    self.app_edit_stub = mock.MagicMock()

    self.application = applications.Application(
        app_edit_stub=self.app_edit_stub
    )

  def test_fetch_process_notebooks(self):
    self.app_edit_stub.FetchProcessNotebooks.return_value = (
        app_edit_service_pb2.FetchProcessNotebooksResponse(
            notebooks={'my_notebook': 'abcd'}
        )
    )

    self.assertEqual(
        self.application.fetch_process_notebooks(),
        {'my_notebook': 'abcd'},
    )
    self.app_edit_stub.FetchProcessNotebooks.assert_called_once()

  def test_save_process_notebooks(self):
    self.app_edit_stub.SaveProcessNotebooks.return_value = (
        app_edit_service_pb2.SaveProcessNotebooksResponse()
    )

    self.application.save_process_notebooks(notebooks={'my_notebook': 'abcd'})

    self.app_edit_stub.SaveProcessNotebooks.assert_called_once()


if __name__ == '__main__':
  absltest.main()
