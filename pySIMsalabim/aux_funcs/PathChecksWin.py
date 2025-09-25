"""Check and convert Windows paths to long path format if necessary."""
# Description:
# ------------
# This script checks if a given Windows path exceeds the traditional MAX_PATH limit
# and converts it to a long path format if necessary.

######### Package Imports ###################################################################

from pathlib import Path

######### Function Definitions ##############################################################

def convert_to_long_path(tempPath):
    """ Convert a path to a Windows long path by adding the \\\\?\\ prefix

    Parameters
    ----------
    tempPath : string
        Path to be converted

    Returns
    -------
    Path
        Converted Path object with long path prefix
    """
    resolved_path = Path(tempPath).resolve()
    if len(str(resolved_path)) < 260: # Windows path length limit
        return resolved_path 
    
    else:
        print(f"\n Warning: Path is too long ({len(resolved_path)} characters), if the process fails try to shorten the path (i.e. by moving the folder to a location with a shorter path). \n If it stills fails try changing the Windows registry to enable long paths: https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=registry#enabling-long-paths-in-windows-10-version-1607-and-later \n Current Path: {tempPath}")

        # Add \\?\ prefix manually for long paths
        win_path = Path("\\\\?\\" + str(resolved_path))
        return win_path
    