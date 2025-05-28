from supabase import create_client, Client
import os

# Environment variables must be set in Render's dashboard
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://dhpyngyubsvyeunevpet.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRocHluZ3l1YnN2eWV1bmV2cGV0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0ODM3OTA4NCwiZXhwIjoyMDYzOTU1MDg0fQ.Tyofi2Y4h3YtF34ot-e4Ea0GpDB43_aArQ0zx-8nVmU")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
