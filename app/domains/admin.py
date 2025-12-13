import os
import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from typing import List, Optional
from pydantic import BaseModel
from app.utils import get_db, engine
from app.models import Product, PlantDetection
import secrets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# ROUTER DEFINITION
# ============================================================================
router = APIRouter(prefix="/admin", tags=["Admin"])
security = HTTPBasic()

# ============================================================================
# CONFIGURATION
# ============================================================================
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change_this_password")

# ============================================================================
# AUTHENTICATION
# ============================================================================
def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials"""
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# ============================================================================
# PYDANTIC MODELS
# ============================================================================
class ProductBase(BaseModel):
    scientific_name: str
    disease: Optional[str] = None
    disease_scientific_name: Optional[str] = None
    product_link: Optional[str] = None
    product_name: Optional[str] = None
    how_to_use: Optional[str] = None
    product_image: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    product_link: Optional[str] = None
    product_name: Optional[str] = None
    how_to_use: Optional[str] = None
    product_image: Optional[str] = None

class ProductResponse(ProductBase):
    id: int
    
    class Config:
        from_attributes = True

class UnmappedProduct(BaseModel):
    scientific_name: str
    disease: str
    disease_scientific_name: str
    detection_count: int

# ============================================================================
# ADMIN PANEL HTML
# ============================================================================
@router.get("/", response_class=HTMLResponse)
async def admin_panel(username: str = Depends(verify_admin)):
    """Serve admin panel HTML"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Garden Genie - Admin Portal</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            
            .header {
                background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            
            .header h1 {
                font-size: 2em;
                margin-bottom: 10px;
            }
            
            .tabs {
                display: flex;
                background: #f8f9fa;
                border-bottom: 2px solid #e9ecef;
            }
            
            .tab {
                flex: 1;
                padding: 20px;
                text-align: center;
                cursor: pointer;
                font-weight: 600;
                color: #495057;
                transition: all 0.3s;
                border: none;
                background: none;
                font-size: 16px;
            }
            
            .tab:hover {
                background: #e9ecef;
            }
            
            .tab.active {
                background: white;
                color: #16a34a;
                border-bottom: 3px solid #16a34a;
            }
            
            .tab-content {
                display: none;
                padding: 30px;
            }
            
            .tab-content.active {
                display: block;
            }
            
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }
            
            .stat-card h3 {
                font-size: 2em;
                margin-bottom: 5px;
            }
            
            .stat-card p {
                opacity: 0.9;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                background: white;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                border-radius: 8px;
                overflow: hidden;
            }
            
            th {
                background: #16a34a;
                color: white;
                padding: 15px;
                text-align: left;
                font-weight: 600;
            }
            
            td {
                padding: 15px;
                border-bottom: 1px solid #e9ecef;
            }
            
            tr:hover {
                background: #f8f9fa;
            }
            
            .btn {
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s;
                margin: 5px;
            }
            
            .btn-primary {
                background: #16a34a;
                color: white;
            }
            
            .btn-primary:hover {
                background: #15803d;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(22, 163, 74, 0.4);
            }
            
            .btn-secondary {
                background: #6c757d;
                color: white;
            }
            
            .btn-secondary:hover {
                background: #5a6268;
            }
            
            .btn-danger {
                background: #dc3545;
                color: white;
            }
            
            .btn-danger:hover {
                background: #c82333;
            }
            
            .modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 1000;
                align-items: center;
                justify-content: center;
            }
            
            .modal.active {
                display: flex;
            }
            
            .modal-content {
                background: white;
                padding: 30px;
                border-radius: 12px;
                max-width: 600px;
                width: 90%;
                max-height: 90vh;
                overflow-y: auto;
            }
            
            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .modal-header h2 {
                color: #16a34a;
            }
            
            .close {
                font-size: 28px;
                cursor: pointer;
                color: #6c757d;
            }
            
            .close:hover {
                color: #dc3545;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #495057;
            }
            
            .form-group input,
            .form-group textarea {
                width: 100%;
                padding: 12px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 14px;
                transition: border-color 0.3s;
            }
            
            .form-group input:focus,
            .form-group textarea:focus {
                outline: none;
                border-color: #16a34a;
            }
            
            .form-group textarea {
                min-height: 100px;
                resize: vertical;
            }
            
            .readonly {
                background: #f8f9fa;
                cursor: not-allowed;
            }
            
            .loading {
                text-align: center;
                padding: 40px;
                color: #6c757d;
            }
            
            .empty-state {
                text-align: center;
                padding: 60px 20px;
                color: #6c757d;
            }
            
            .empty-state svg {
                width: 100px;
                height: 100px;
                margin-bottom: 20px;
                opacity: 0.3;
            }
            
            .search-box {
                margin-bottom: 20px;
                display: flex;
                gap: 10px;
            }
            
            .search-box input {
                flex: 1;
                padding: 12px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 14px;
            }
            
            .image-preview {
                max-width: 100px;
                max-height: 100px;
                border-radius: 4px;
                cursor: pointer;
            }
            
            .image-preview:hover {
                opacity: 0.8;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌱 Garden Genie Admin Portal</h1>
                <p>Product Management Dashboard</p>
            </div>
            
            <div class="tabs">
                <button class="tab active" onclick="switchTab('unmapped')">
                    Unmapped Products
                </button>
                <button class="tab" onclick="switchTab('mapped')">
                    Existing Products
                </button>
            </div>
            
            <!-- Unmapped Products Tab -->
            <div id="unmapped" class="tab-content active">
                <div class="stats">
                    <div class="stat-card">
                        <h3 id="unmapped-count">-</h3>
                        <p>Unmapped Detections</p>
                    </div>
                    <div class="stat-card">
                        <h3 id="total-detections">-</h3>
                        <p>Total Detections</p>
                    </div>
                </div>
                
                <div class="search-box">
                    <input type="text" id="unmapped-search" placeholder="Search by plant or disease..." onkeyup="filterUnmapped()">
                    <button class="btn btn-primary" onclick="loadUnmapped()">Refresh</button>
                </div>
                
                <div id="unmapped-table-container"></div>
            </div>
            
            <!-- Mapped Products Tab -->
            <div id="mapped" class="tab-content">
                <div class="stats">
                    <div class="stat-card">
                        <h3 id="mapped-count">-</h3>
                        <p>Total Products</p>
                    </div>
                </div>
                
                <div class="search-box">
                    <input type="text" id="mapped-search" placeholder="Search products..." onkeyup="filterMapped()">
                    <button class="btn btn-primary" onclick="loadMapped()">Refresh</button>
                </div>
                
                <div id="mapped-table-container"></div>
            </div>
        </div>
        
        <!-- Add Product Modal -->
        <div id="add-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Add New Product</h2>
                    <span class="close" onclick="closeModal('add-modal')">&times;</span>
                </div>
                <form id="add-form" onsubmit="addProduct(event)">
                    <div class="form-group">
                        <label>Plant (Scientific Name) *</label>
                        <input type="text" id="add-scientific-name" class="readonly" readonly required>
                    </div>
                    <div class="form-group">
                        <label>Disease (Common Name) *</label>
                        <input type="text" id="add-disease" class="readonly" readonly required>
                    </div>
                    <div class="form-group">
                        <label>Disease (Scientific Name) *</label>
                        <input type="text" id="add-disease-scientific" class="readonly" readonly required>
                    </div>
                    <div class="form-group">
                        <label>Product Name *</label>
                        <input type="text" id="add-product-name" required>
                    </div>
                    <div class="form-group">
                        <label>Product Link (URL) *</label>
                        <input type="url" id="add-product-link" required placeholder="https://gardengenie.in/product/...">
                    </div>
                    <div class="form-group">
                        <label>How to Use *</label>
                        <textarea id="add-how-to-use" required placeholder="Enter usage instructions..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>Product Image URL *</label>
                        <input type="url" id="add-product-image" required placeholder="https://gardengenie.in/wp-content/uploads/...">
                    </div>
                    <div style="text-align: right;">
                        <button type="button" class="btn btn-secondary" onclick="closeModal('add-modal')">Cancel</button>
                        <button type="submit" class="btn btn-primary">Add Product</button>
                    </div>
                </form>
            </div>
        </div>
        
        <!-- Edit Product Modal -->
        <div id="edit-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Edit Product</h2>
                    <span class="close" onclick="closeModal('edit-modal')">&times;</span>
                </div>
                <form id="edit-form" onsubmit="updateProduct(event)">
                    <input type="hidden" id="edit-product-id">
                    <div class="form-group">
                        <label>Plant (Scientific Name)</label>
                        <input type="text" id="edit-scientific-name" class="readonly" readonly>
                    </div>
                    <div class="form-group">
                        <label>Disease (Common Name)</label>
                        <input type="text" id="edit-disease" class="readonly" readonly>
                    </div>
                    <div class="form-group">
                        <label>Disease (Scientific Name)</label>
                        <input type="text" id="edit-disease-scientific" class="readonly" readonly>
                    </div>
                    <div class="form-group">
                        <label>Product Name *</label>
                        <input type="text" id="edit-product-name" required>
                    </div>
                    <div class="form-group">
                        <label>Product Link (URL) *</label>
                        <input type="url" id="edit-product-link" required>
                    </div>
                    <div class="form-group">
                        <label>How to Use *</label>
                        <textarea id="edit-how-to-use" required></textarea>
                    </div>
                    <div class="form-group">
                        <label>Product Image URL *</label>
                        <input type="url" id="edit-product-image" required>
                    </div>
                    <div style="text-align: right;">
                        <button type="button" class="btn btn-danger" onclick="deleteProduct()">Delete</button>
                        <button type="button" class="btn btn-secondary" onclick="closeModal('edit-modal')">Cancel</button>
                        <button type="submit" class="btn btn-primary">Update Product</button>
                    </div>
                </form>
            </div>
        </div>
        
        <script>
            let unmappedData = [];
            let mappedData = [];
            
            // Switch between tabs
            function switchTab(tabName) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
                
                event.target.classList.add('active');
                document.getElementById(tabName).classList.add('active');
                
                if (tabName === 'unmapped') {
                    loadUnmapped();
                } else {
                    loadMapped();
                }
            }
            
            // Load unmapped products
            async function loadUnmapped() {
                const container = document.getElementById('unmapped-table-container');
                container.innerHTML = '<div class="loading">Loading unmapped products...</div>';
                
                try {
                    const response = await fetch('/admin/api/unmapped-products');
                    if (!response.ok) {
                        const error = await response.text();
                        throw new Error(error);
                    }
                    
                    unmappedData = await response.json();
                    document.getElementById('unmapped-count').textContent = unmappedData.length;
                    
                    if (unmappedData.length === 0) {
                        container.innerHTML = `
                            <div class="empty-state">
                                <p>✅ All detections have product mappings!</p>
                            </div>
                        `;
                        return;
                    }
                    
                    renderUnmappedTable(unmappedData);
                } catch (error) {
                    container.innerHTML = '<div class="loading">Error loading data: ' + error.message + '</div>';
                    console.error(error);
                }
            }
            
            // Render unmapped table
            function renderUnmappedTable(data) {
                const container = document.getElementById('unmapped-table-container');
                
                const html = `
                    <table>
                        <thead>
                            <tr>
                                <th>Plant (Scientific)</th>
                                <th>Disease</th>
                                <th>Disease (Scientific)</th>
                                <th>Detections</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.map(item => `
                                <tr>
                                    <td>${item.scientific_name || 'N/A'}</td>
                                    <td>${item.disease || 'N/A'}</td>
                                    <td>${item.disease_scientific_name || 'N/A'}</td>
                                    <td>${item.detection_count}</td>
                                    <td>
                                        <button class="btn btn-primary" onclick='openAddModal(${JSON.stringify(item)})'>
                                            Add Product
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
                
                container.innerHTML = html;
            }
            
            // Load mapped products
            async function loadMapped() {
                const container = document.getElementById('mapped-table-container');
                container.innerHTML = '<div class="loading">Loading products...</div>';
                
                try {
                    const response = await fetch('/admin/api/products');
                    if (!response.ok) throw new Error('Failed to load');
                    
                    mappedData = await response.json();
                    document.getElementById('mapped-count').textContent = mappedData.length;
                    
                    if (mappedData.length === 0) {
                        container.innerHTML = `
                            <div class="empty-state">
                                <p>No products found</p>
                            </div>
                        `;
                        return;
                    }
                    
                    renderMappedTable(mappedData);
                } catch (error) {
                    container.innerHTML = '<div class="loading">Error loading data</div>';
                    console.error(error);
                }
            }
            
            // Render mapped table
            function renderMappedTable(data) {
                const container = document.getElementById('mapped-table-container');
                
                const html = `
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Plant</th>
                                <th>Disease</th>
                                <th>Product</th>
                                <th>Image</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.map(item => `
                                <tr>
                                    <td>${item.id}</td>
                                    <td>${item.scientific_name || 'N/A'}</td>
                                    <td>${item.disease_scientific_name || 'N/A'}</td>
                                    <td>${item.product_name || 'N/A'}</td>
                                    <td>
                                        ${item.product_image ? 
                                            `<img src="${item.product_image}" class="image-preview" onclick="window.open('${item.product_image}', '_blank')">` 
                                            : 'N/A'}
                                    </td>
                                    <td>
                                        <button class="btn btn-primary" onclick='openEditModal(${JSON.stringify(item)})'>
                                            Edit
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
                
                container.innerHTML = html;
            }
            
            // Filter unmapped
            function filterUnmapped() {
                const search = document.getElementById('unmapped-search').value.toLowerCase();
                const filtered = unmappedData.filter(item => 
                    (item.scientific_name && item.scientific_name.toLowerCase().includes(search)) ||
                    (item.disease && item.disease.toLowerCase().includes(search)) ||
                    (item.disease_scientific_name && item.disease_scientific_name.toLowerCase().includes(search))
                );
                renderUnmappedTable(filtered);
            }
            
            // Filter mapped
            function filterMapped() {
                const search = document.getElementById('mapped-search').value.toLowerCase();
                const filtered = mappedData.filter(item => 
                    (item.scientific_name && item.scientific_name.toLowerCase().includes(search)) ||
                    (item.disease && item.disease.toLowerCase().includes(search)) ||
                    (item.product_name && item.product_name.toLowerCase().includes(search))
                );
                renderMappedTable(filtered);
            }
            
            // Open add modal
            function openAddModal(item) {
                document.getElementById('add-scientific-name').value = item.scientific_name || '';
                document.getElementById('add-disease').value = item.disease || '';
                document.getElementById('add-disease-scientific').value = item.disease_scientific_name || '';
                document.getElementById('add-product-name').value = '';
                document.getElementById('add-product-link').value = '';
                document.getElementById('add-how-to-use').value = '';
                document.getElementById('add-product-image').value = '';
                
                document.getElementById('add-modal').classList.add('active');
            }
            
            // Open edit modal
            function openEditModal(item) {
                document.getElementById('edit-product-id').value = item.id;
                document.getElementById('edit-scientific-name').value = item.scientific_name || '';
                document.getElementById('edit-disease').value = item.disease || '';
                document.getElementById('edit-disease-scientific').value = item.disease_scientific_name || '';
                document.getElementById('edit-product-name').value = item.product_name || '';
                document.getElementById('edit-product-link').value = item.product_link || '';
                document.getElementById('edit-how-to-use').value = item.how_to_use || '';
                document.getElementById('edit-product-image').value = item.product_image || '';
                
                document.getElementById('edit-modal').classList.add('active');
            }
            
            // Close modal
            function closeModal(modalId) {
                document.getElementById(modalId).classList.remove('active');
            }
            
            // Add product
            async function addProduct(event) {
                event.preventDefault();
                
                const data = {
                    scientific_name: document.getElementById('add-scientific-name').value,
                    disease: document.getElementById('add-disease').value,
                    disease_scientific_name: document.getElementById('add-disease-scientific').value,
                    product_name: document.getElementById('add-product-name').value,
                    product_link: document.getElementById('add-product-link').value,
                    how_to_use: document.getElementById('add-how-to-use').value,
                    product_image: document.getElementById('add-product-image').value
                };
                
                try {
                    const response = await fetch('/admin/api/products', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(data)
                    });
                    
                    if (!response.ok) throw new Error('Failed to add product');
                    
                    alert('Product added successfully!');
                    closeModal('add-modal');
                    loadUnmapped();
                    loadMapped();
                } catch (error) {
                    alert('Error adding product: ' + error.message);
                }
            }
            
            // Update product
            async function updateProduct(event) {
                event.preventDefault();
                
                const id = document.getElementById('edit-product-id').value;
                const data = {
                    product_name: document.getElementById('edit-product-name').value,
                    product_link: document.getElementById('edit-product-link').value,
                    how_to_use: document.getElementById('edit-how-to-use').value,
                    product_image: document.getElementById('edit-product-image').value
                };
                
                try {
                    const response = await fetch(`/admin/api/products/${id}`, {
                        method: 'PUT',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(data)
                    });
                    
                    if (!response.ok) throw new Error('Failed to update product');
                    
                    alert('Product updated successfully!');
                    closeModal('edit-modal');
                    loadMapped();
                } catch (error) {
                    alert('Error updating product: ' + error.message);
                }
            }
            
            // Delete product
            async function deleteProduct() {
                if (!confirm('Are you sure you want to delete this product?')) return;
                
                const id = document.getElementById('edit-product-id').value;
                
                try {
                    const response = await fetch(`/admin/api/products/${id}`, {
                        method: 'DELETE'
                    });
                    
                    if (!response.ok) throw new Error('Failed to delete product');
                    
                    alert('Product deleted successfully!');
                    closeModal('edit-modal');
                    loadMapped();
                } catch (error) {
                    alert('Error deleting product: ' + error.message);
                }
            }
            
            // Load initial data
            loadUnmapped();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get("/api/unmapped-products", response_model=List[UnmappedProduct])
async def get_unmapped_products(
    username: str = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """
    Get all unique plant+disease combinations from PlantDetection 
    that don't have corresponding products.
    
    Handles:
    - JSON arrays in disease fields
    - NULL disease_scientific_name (for abiotic/healthy cases)
    - Case-insensitive comparison
    """
    try:
        # Get all detections from database
        all_detections = db.query(PlantDetection).all()
        logger.info(f"Total detections in database: {len(all_detections)}")
        
        # Get all existing products
        products = db.query(Product).all()
        logger.info(f"Total products in database: {len(products)}")
        
        # Build set of existing product combinations
        existing_combinations = set()
        for p in products:
            if p.scientific_name and p.disease_scientific_name:
                # Normalize for comparison
                key = (
                    p.scientific_name.lower().strip(),
                    p.disease_scientific_name.lower().strip()
                )
                existing_combinations.add(key)
        
        logger.info(f"Existing product combinations: {len(existing_combinations)}")
        
        # Process detections to extract unique combinations
        detection_map = {}
        skipped_no_plant = 0
        skipped_no_disease = 0
        skipped_healthy = 0
        
        for detection in all_detections:
            scientific_name = detection.scientific_name
            
            # Skip if no plant name
            if not scientific_name:
                skipped_no_plant += 1
                continue
            
            # Handle disease fields - they could be arrays or strings
            if isinstance(detection.disease, list):
                disease_list = detection.disease
            elif detection.disease:
                disease_list = [detection.disease]
            else:
                disease_list = []
            
            if isinstance(detection.disease_scientific_name, list):
                disease_sci_list = detection.disease_scientific_name
            elif detection.disease_scientific_name:
                disease_sci_list = [detection.disease_scientific_name]
            else:
                disease_sci_list = []
            
            # Get first element from arrays
            disease = disease_list[0] if disease_list and len(disease_list) > 0 else None
            disease_scientific = disease_sci_list[0] if disease_sci_list and len(disease_sci_list) > 0 else None
            
            # Skip if no disease at all
            if not disease:
                skipped_no_disease += 1
                continue
            
            # Skip "Healthy" plants - they don't need products
            if disease and "healthy" in disease.lower():
                skipped_healthy += 1
                continue
            
            # For abiotic cases (NULL disease_scientific_name), use disease common name
            if not disease_scientific:
                # Use the common disease name as the scientific name for matching
                disease_scientific = disease
            
            # Create unique key (normalized)
            key = (
                scientific_name.lower().strip(),
                disease_scientific.lower().strip()
            )
            
            # Check if this combination exists in products
            if key not in existing_combinations:
                # Use original (non-normalized) values for display
                display_key = (scientific_name, disease, disease_scientific)
                if display_key not in detection_map:
                    detection_map[display_key] = {
                        "scientific_name": scientific_name,
                        "disease": disease,
                        "disease_scientific_name": disease_scientific,
                        "detection_count": 0
                    }
                detection_map[display_key]["detection_count"] += 1
        
        # Convert to list
        unmapped = list(detection_map.values())
        
        # Sort by detection count (highest first)
        unmapped.sort(key=lambda x: x["detection_count"], reverse=True)
        
        logger.info(f"Skipped - No plant name: {skipped_no_plant}")
        logger.info(f"Skipped - No disease: {skipped_no_disease}")
        logger.info(f"Skipped - Healthy plants: {skipped_healthy}")
        logger.info(f"Found {len(unmapped)} unmapped product combinations")
        
        return unmapped
        
    except Exception as e:
        logger.error(f"Error fetching unmapped products: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/products", response_model=List[ProductResponse])
async def get_all_products(
    username: str = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Get all existing products (deduplicated by unique combinations)"""
    try:
        products = db.query(Product).order_by(Product.id.desc()).all()
        logger.info(f"Retrieved {len(products)} products")
        return products
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/products", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    username: str = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Add a new product"""
    try:
        # Check if product already exists for this exact combination
        existing = db.query(Product).filter(
            and_(
                Product.scientific_name == product.scientific_name,
                Product.disease_scientific_name == product.disease_scientific_name
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Product already exists for this plant+disease combination"
            )
        
        db_product = Product(**product.dict())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        
        logger.info(f"Created product: {db_product.id}")
        return db_product
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    username: str = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Update an existing product"""
    try:
        db_product = db.query(Product).filter(Product.id == product_id).first()
        
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Update only the fields that can be edited
        update_data = product_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_product, key, value)
        
        db.commit()
        db.refresh(db_product)
        
        logger.info(f"Updated product: {product_id}")
        return db_product
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/products/{product_id}")
async def delete_product(
    product_id: int,
    username: str = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Delete a product"""
    try:
        db_product = db.query(Product).filter(Product.id == product_id).first()
        
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        db.delete(db_product)
        db.commit()
        
        logger.info(f"Deleted product: {product_id}")
        return {"message": "Product deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/stats")
async def get_stats(
    username: str = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    try:
        total_products = db.query(Product).count()
        total_detections = db.query(PlantDetection).count()
        
        # Get unmapped products using the same logic as get_unmapped_products
        all_detections = db.query(PlantDetection).all()
        products = db.query(Product).all()
        existing_combinations = {
            (p.scientific_name, p.disease_scientific_name) 
            for p in products
            if p.scientific_name and p.disease_scientific_name
        }
        
        unique_combinations = set()
        unmapped_combinations = set()
        
        for detection in all_detections:
            scientific_name = detection.scientific_name
            disease_list = detection.disease if isinstance(detection.disease, list) else []
            disease_sci_list = detection.disease_scientific_name if isinstance(detection.disease_scientific_name, list) else []
            
            disease_scientific = disease_sci_list[0] if disease_sci_list and len(disease_sci_list) > 0 else None
            
            if not scientific_name or not disease_scientific:
                continue
            
            key = (scientific_name, disease_scientific)
            unique_combinations.add(key)
            
            if key not in existing_combinations:
                unmapped_combinations.add(key)
        
        return {
            "total_products": total_products,
            "total_detections": total_detections,
            "unmapped_count": len(unmapped_combinations),
            "unique_detections": len(unique_combinations)
        }
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))