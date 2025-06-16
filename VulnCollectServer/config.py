import os

DEFECTDOJO_URL = os.getenv("DEFECTDOJO_URL", "http://defectdojo:8080/api/v2/import-scan/")
DEFECTDOJO_API_KEY = os.getenv("DEFECTDOJO_API_KEY", "dummy-api-key")
DEFECTDOJO_ENGAGEMENT_ID = int(os.getenv("DEFECTDOJO_ENGAGEMENT_ID", "1"))
DEFECTDOJO_SCAN_TYPE = os.getenv("DEFECTDOJO_SCAN_TYPE", "Generic Findings Import")

LIST_OF_TOOLS = os.getenv("LIST_OF_TOOLS", "tool1,tool2").split(",")
