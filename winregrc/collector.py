# -*- coding: utf-8 -*-
"""Windows volume collector."""

from __future__ import unicode_literals

from dfvfs.helpers import volume_scanner as dfvfs_volume_scanner
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as dfvfs_path_spec_factory
from dfvfs.resolver import resolver as dfvfs_resolver

from dfwinreg import interface as dfwinreg_interface
from dfwinreg import regf as dfwinreg_regf
from dfwinreg import registry as dfwinreg_registry


class CollectorRegistryFileReader(dfwinreg_interface.WinRegistryFileReader):
  """Collector-based Windows Registry file reader."""

  def __init__(self, volume_scanner):
    """Initializes a Windows Registry file reader object.

    Args:
      volume_scanner (dfvfs.WindowsVolumeScanner): Windows volume scanner.
    """
    super(CollectorRegistryFileReader, self).__init__()
    self._volume_scanner = volume_scanner

  def Open(self, path, ascii_codepage='cp1252'):
    """Opens the Windows Registry file specified by the path.

    Args:
      path (str): path of the Windows Registry file. The path is a Windows
          path relative to the root of the file system that contains the
          specific Windows Registry file, such as:
          C:\\Windows\\System32\\config\\SYSTEM
      ascii_codepage (Optional[str]): ASCII string codepage.

    Returns:
      WinRegistryFile: Windows Registry file or None the file does not exist or
          cannot be opened.
    """
    file_object = self._volume_scanner.OpenFile(path)
    if file_object is None:
      return None

    registry_file = dfwinreg_regf.REGFWinRegistryFile(
        ascii_codepage=ascii_codepage)

    try:
      registry_file.Open(file_object)
    except IOError:
      file_object.close()
      return None

    return registry_file


class WindowsRegistryCollector(dfvfs_volume_scanner.WindowsVolumeScanner):
  """Windows Registry collector.

  Attributes:
    registry (dfwinreg.WinRegistry): Windows Registry.
  """

  def __init__(self, mediator=None):
    """Initializes a Windows Registry collector.

    Args:
      mediator (Optional[dfvfs.VolumeScannerMediator]): a volume scanner
          mediator.
    """
    super(WindowsRegistryCollector, self).__init__(mediator=mediator)
    self._single_file = False
    registry_file_reader = CollectorRegistryFileReader(self)
    self.registry = dfwinreg_registry.WinRegistry(
        registry_file_reader=registry_file_reader)

  def IsSingleFileRegistry(self):
    """Determines if the Registry consists of a single file.

    Returns:
      bool: True if the Registry consists of a single file.
    """
    return self._single_file

  def OpenFile(self, windows_path):
    """Opens the file specified by the Windows path.

    Args:
      windows_path (str): Windows path to the file.

    Returns:
      dfvfs.FileIO: file-like object or None if the file does not exist.
    """
    if not self._single_file:
      return super(WindowsRegistryCollector, self).OpenFile(windows_path)

    # TODO: check name of single file.
    path_spec = dfvfs_path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=self._source_path)
    if path_spec is None:
      return None

    return dfvfs_resolver.Resolver.OpenFileObject(path_spec)

  def ScanForWindowsVolume(self, source_path):
    """Scans for a Windows volume.

    Args:
      source_path (str): source path.

    Returns:
      bool: True if a Windows volume was found.

    Raises:
      ScannerError: if the source path does not exists, or if the source path
          is not a file or directory, or if the format of or within
          the source file is not supported.
    """
    result = super(WindowsRegistryCollector, self).ScanForWindowsVolume(
        source_path)

    if self._source_type == dfvfs_definitions.SOURCE_TYPE_FILE:
      self._single_file = True
      return True

    return result
