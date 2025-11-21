import os
import logging
import warnings
# SUPPRESS GOOGLE CLOUD WARNINGS - MUST BE AT THE TOP
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'
warnings.filterwarnings("ignore", category=UserWarning, module="google.auth")
logging.getLogger('google').setLevel(logging.ERROR)
logging.getLogger('googleapiclient').setLevel(logging.ERROR)
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from datetime import datetime
# Load environment
# Load environment variables
load_dotenv()
# Import pipeline functions
from src.pipeline.unified_news_pipeline import execute_complete_pipeline
app = FastAPI(
    title="AI News Memes Generator",
    description="Single-click endpoint for complete news scraping and AI meme generation pipeline",
    version="3.0.0"
)
# Global variables for pipeline configuration
template_client = None  # Organization Supabase for templates
storage_client = None   # Personal Supabase for storage/table
gemini_api_key = None
bucket_name = os.getenv('STORAGE_SUPABASE_BUCKET_NAME', 'assets')  # Personal bucket

def initialize_pipeline():
    """Initialize the pipeline configuration with dual Supabase clients"""
    global template_client, storage_client, gemini_api_key
   
    try:
        # Organization Supabase (templates)
        org_url = os.getenv('SUPABASE_URL')
        org_key = os.getenv('SUPABASE_KEY')
        if not org_url or not org_key:
            raise Exception("Missing SUPABASE_URL or SUPABASE_KEY in .env file (organization)")
        template_client = create_client(org_url, org_key)
        template_client.postgrest.session.headers.update({'Accept-Profile': 'dc'})
        print(" SUCCESS: Organization Supabase client configured for 'dc' schema")
        
        # Verify organization tables
        try:
            emotions_result = template_client.table('emotions').select('*').limit(1).execute()
            memes_result = template_client.table('memes_dc').select('*').limit(1).execute()
            print(f" SUCCESS: Organization tables accessible - emotions: {len(emotions_result.data)}, memes_dc: {len(memes_result.data)}")
        except Exception as verify_e:
            print(f" Organization schema verification failed: {str(verify_e)}")
            raise Exception(f"Organization schema access failed: {str(verify_e)}")
       
        # Personal Supabase (storage/table)
        storage_url = os.getenv('STORAGE_SUPABASE_URL')
        storage_key = os.getenv('STORAGE_SUPABASE_KEY')
        if not storage_url or not storage_key:
            raise Exception("Missing STORAGE_SUPABASE_URL or STORAGE_SUPABASE_KEY in .env file (personal)")
        storage_client = create_client(storage_url, storage_key)
        print(" SUCCESS: Personal Supabase client configured for public schema")
        
        # Verify personal table
        try:
            table_result = storage_client.table('trending_news').select('*').limit(1).execute()
            print(f" SUCCESS: Personal table accessible - {len(table_result.data)} records")
        except Exception as verify_e:
            print(f" Personal table verification failed: {str(verify_e)}")
            raise Exception(f"Personal table access failed: {str(verify_e)}")
       
        # Verify personal bucket
        try:
            buckets = storage_client.storage.list_buckets().data
            if bucket_name not in [b.name for b in buckets]:
                print(f" WARNING: Personal bucket '{bucket_name}' not found; create it in personal Supabase dashboard.")
        except:
            pass
       
        # Get Gemini API key
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            raise Exception("No GEMINI_API_KEY found in .env file")
       
        print(" Pipeline configuration initialized successfully!")
        print(f" - Organization Supabase: Templates/emotions (dc schema)")
        print(f" - Personal Supabase: Storage/table (public schema), Bucket: {bucket_name}")
        print(f" - Gemini API Key: Single key configured")
       
        return True
       
    except Exception as e:
        print(f" Pipeline initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
# Initialize pipeline configuration
pipeline_ready = initialize_pipeline()
@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "api": "AI News Memes Generator",
        "version": "3.0.0",
        "description": "One-click complete pipeline for AI-powered news meme generation with dual Supabase persistence",
        "status": "Ready" if pipeline_ready else "Not initialized",
        "main_endpoint": "/ai-memes",
        "usage": "Simply click on /ai-memes endpoint to generate all memes",
        "process": [
            "Scrapes latest news from 18+ Indian sources",
            "Processes and ranks articles by buzz score",
            "AI processes articles for LLM description, emotion, and sarcasm (organization Supabase for templates)",
            "Matches emotion-based meme templates",
            "Overlays single-line dialogues on templates",
            "Generates final memes and uploads to personal Supabase storage",
            "Inserts data to personal trending_news table with meme URLs (sortable by scraped_at DESC)"
        ],
        "categories": ["politics", "movies", "entertainment", "sports", "business", "technology"],
        "dialogue_format": "Single-line Tnglish dialogues under 10 words each",
        "architecture": "MLOps pipeline with dual Supabase (organization for templates, personal for storage/DB; no base64 in DB)",
        "storage_bucket": bucket_name
    }
@app.get("/ai-memes")
def generate_ai_memes():
    """
    ONE-CLICK AI MEMES GENERATOR
   
    Single endpoint that executes the complete end-to-end pipeline with dual Supabase persistence.
    """
    if not pipeline_ready:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "AI Memes Generator not ready",
                "message": "Pipeline initialization failed. Check your .env configuration for Supabase (org/personal) and Gemini API key",
                "required_env_vars": ["SUPABASE_URL", "SUPABASE_KEY", "STORAGE_SUPABASE_URL", "STORAGE_SUPABASE_KEY", "GEMINI_API_KEY"],
                "timestamp": datetime.now().isoformat()
            }
        )
   
    try:
        print("\n" + "="*80)
        print(" AI NEWS MEMES GENERATOR - COMPLETE PIPELINE STARTING")
        print("="*80)
       
        # Execute the complete pipeline with dual clients
        result = execute_complete_pipeline(gemini_api_key, template_client, storage_client)
       
        print("\n" + "="*80)
        print(" AI MEMES GENERATION COMPLETED SUCCESSFULLY!")
        print("="*80 + "\n")
       
        return JSONResponse(content=result)
       
    except Exception as e:
        clean_error = str(e)
        if "ALTS creds ignored" in clean_error:
            clean_error = clean_error.replace("ALTS creds ignored. Not running on GCP and untrusted ALTS is not enabled.", "").strip()
       
        print(f"ERROR: AI Memes generation failed: {clean_error}")
       
        raise HTTPException(
            status_code=500,
            detail={
                "error": "AI Memes generation failed",
                "message": clean_error,
                "timestamp": datetime.now().isoformat(),
                "suggestion": "Check server logs for detailed error information",
                "retry": "You can try the /ai-memes endpoint again"
            }
        )
if __name__ == "__main__":
    import uvicorn
   
    print("="*80)
    print(" AI NEWS MEMES GENERATOR API")
    print("="*80)
   
    if pipeline_ready:
        print("Pipeline Ready!")
        print("Main Endpoint: http://localhost:8000/ai-memes")
        print("API Info: http://localhost:8000/")
        print("\nONE-CLICK PROCESS:")
        print(" Click /ai-memes -> Complete pipeline executes automatically")
        print(" Takes ~3-5 minutes to process 60+ articles")
        print(" Uses organization Supabase for templates; personal for storage/DB")
        print("\nFeatures:")
        print(" • Single-click meme generation with dual Supabase")
        print(" • MLOps pipeline with single Gemini API key")
        print(" • 60+ categorized news articles processed and inserted")
        print(" • AI-powered sarcastic Tnglish content and LLM descriptions")
        print(" • Single-line dialogues under 10 words each")
        print(" • Emotion-based template matching")
        print(" • Dynamic font sizing and overlay")
        print(" • Meme URLs in personal Supabase (no base64; sortable by timestamp)")
    else:
        print("Pipeline initialization failed")
        print(" Check your .env file configuration")
        print(" Required: SUPABASE_URL, SUPABASE_KEY (org), STORAGE_SUPABASE_URL, STORAGE_SUPABASE_KEY (personal), GEMINI_API_KEY")
        print(" Optional: STORAGE_SUPABASE_BUCKET_NAME")
        print(" API will still start for debugging")
   
    print("="*80)
    print("Starting server on http://localhost:8000")
    print("="*80)
   
    uvicorn.run(app, host="0.0.0.0", port=8000)