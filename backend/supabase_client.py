from supabase import create_client, Client

# Replace with your values
SUPABASE_URL = "https://dhpyngyubsvyeunevpet.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRocHluZ3l1YnN2eWV1bmV2cGV0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgzNzkwODQsImV4cCI6MjA2Mzk1NTA4NH0.qmCWQItMnrZdhNMtOXmsfV02jDnv537y2tBxf1K-Pg0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
