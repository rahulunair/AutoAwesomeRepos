import re


class LicenseParser:
    """
    A class for detecting the license of a GitHub repository.

    Args:
        repo (GitHubRepo): The GitHub repository to detect the license for.
    """

    LICENSE_REGEX = {
        "MIT License": r"^(MIT License|MIT)",
        "Apache License 2.0": r"^Apache License(?:, Version \d\.\d)?",
        "BSD 2-Clause License": r"^BSD 2-Clause License",
        "BSD 3-Clause License": r"^BSD 3-Clause License",
        "BSD License": r"^BSD",
        "GNU GPL": r"^GNU General Public License",
        "Mozilla Public License": r"^Mozilla Public License",
        "Eclipse Public License": r"^Eclipse Public License",
        "The Unlicense": r"^The Unlicense",
        "ISC License": r"^ISC License",
        "Artistic License 2.0": r"^Artistic License 2\.0",
        "Boost Software License": r"^Boost Software License",
        "CC0 1.0 Universal": r"^CC0 1\.0 Universal",
        "CC-BY 4.0": r"^Creative Commons Attribution 4\.0",
        "CC-BY-SA 4.0": r"^Creative Commons Attribution Share Alike 4\.0",
        "CC-BY-NC 4.0": r"^Creative Commons Attribution Non Commercial 4\.0",
        "Erlang Public License": r"^Erlang Public License",
        "GNU AGPL": r"^GNU Affero General Public License",
        "GNU LGPL": r"^GNU Lesser General Public License",
        "ISC License": r"^ISC License",
        "LPPL 1.3c": r"^LaTeX Project Public License 1\.3c",
        "MPL 2.0": r"^Mozilla Public License 2\.0",
        "ODC-BY 1.0": r"^Open Data Commons Attribution License 1\.0",
        "ODbL 1.0": r"^Open Data Commons Open Database License 1\.0",
        "OFL 1.1": r"^SIL Open Font License 1\.1",
        "PostgreSQL License": r"^PostgreSQL License",
        "Simplified BSD License": r"^Simplified BSD License",
        "WTFPL": r"^WTFPL",
        "Zlib License": r"^Zlib License",
        "Apache License 1.0": r"^Apache License, Version 1\.0",
        "BSD+Patent License": r"^BSD\+Patent",
        "CeCILL-C": r"^CeCILL-C",
        "CeCILL": r"^CeCILL",
        "EUPL 1.1": r"^European Union Public Licence 1\.1",
        "GPLv3 or later": r"^GNU General Public License v3\.0 or later",
        "IBM Public License": r"^IBM Public License",
        "LGPLv3": r"^GNU Lesser General Public License v3\.0",
        "NCSA License": r"^NCSA Open Source License",
    }

    def __init__(self, license_file):
        self.license_file = license_file

    def parse(self):
        if self.license_file is not None:
            license_content = self.license_file.decoded_content.decode()
            license_lines = license_content.split("\n")
            license_first_line = license_lines[0].strip()
            for license_name, license_regex in self.LICENSE_REGEX.items():
                if re.search(license_regex, license_first_line, re.IGNORECASE):
                    return license_name
            if license_first_line == "Apache License":
                license_second_line = license_lines[1].strip()
                if license_second_line.startswith("Version 2.0"):
                    return "Apache License 2.0"

            return "Unknown License"
        return "Unknown License"
