import os
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import markdown
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Markdown to Image API")

# Ensure public directory exists
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "public")
os.makedirs(PUBLIC_DIR, exist_ok=True)

# Mount the public directory for accessing generated images
app.mount("/public", StaticFiles(directory="public"), name="public")

# Setup Jinja2 environment
env = Environment(loader=FileSystemLoader("."))

class MD2ImgRequest(BaseModel):
    content: str = Field(..., description="Markdown text content")
    header: Optional[str] = Field(default=None, description="Optional header text")
    footer: Optional[str] = Field(default=None, description="Optional footer text")
    theme: Optional[str] = Field(default="light", description="Theme (light or dark)")
    width: int = Field(default=800, description="Width of the desired image in pixels")

@app.post("/api/generate_image")
async def generate_image(request: Request, body: MD2ImgRequest):
    try:
        # Convert markdown to HTML
        html_content = markdown.markdown(body.content, extensions=['extra', 'codehilite', 'nl2br'])
        
        # Load and render template
        template = env.get_template("template.html")
        rendered_html = template.render(
            html_content=html_content,
            header=body.header,
            footer=body.footer,
            theme=body.theme,
            width=body.width
        )
        
        # Generate a unique filename
        filename = f"{uuid.uuid4().hex}.png"
        filepath = os.path.join(PUBLIC_DIR, filename)
        
        # Use Playwright to capture screenshot
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            
            # Set viewport with the given width. Height will adapt to content.
            # Emulating device scale factor can improve image sharpness
            context = await browser.new_context(
                viewport={'width': body.width, 'height': 800},
                device_scale_factor=2
            )
            page = await context.new_page()
            
            # Set content
            await page.set_content(rendered_html, wait_until="networkidle")
            
            # Take screenshot of the container element instead of full_page to avoid bottom whitespace
            container = await page.query_selector('.container')
            if container:
                await container.screenshot(path=filepath)
            else:
                await page.screenshot(path=filepath, full_page=True)
            
            await browser.close()
            
        # Build the full URL
        base_url = str(request.base_url).rstrip('/')
        image_url = f"{base_url}/public/{filename}"
        
        return {"url": image_url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
