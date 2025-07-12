from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_API_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

def get_table(name):
    return supabase.table(name)
