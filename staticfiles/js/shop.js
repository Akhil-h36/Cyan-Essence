async function searchProduct(query) {
  if (query === undefined || query === null) {
    query = '';
  }
  
  // Trim the query to remove any leading/trailing whitespace
  query = query.trim();
  
  try {
    const response = await fetch(`shop/search-products?query=${encodeURIComponent(query)}`);
    if (response.ok) {
      const products = await response.json();
      renderSearchResults(products);
    } else {
      console.error('Error fetching products');
    }
  } catch (error) {
    console.error('Fetch error:', error);
  }
}

// Function to render search results dynamically
function renderSearchResults(products) {
  const resultsContainer = document.getElementById('search-results');
  resultsContainer.innerHTML = ''; // Clear previous results

  if (products.length === 0) {
    resultsContainer.innerHTML = '<p>No products found</p>';
    return;
  }

  products.forEach(product => {
    const rating = product.averageRating || 0;
    const stars = Array(5).fill(0).map((_, i) => 
      `<i class="fas fa-star ${i < rating ? '' : 'far'}"></i>`
    ).join('');

    const productCard = `
      <div class="col-md-4 col-sm-6">
        <div class="card h-100 shadow-sm border-1 ${product.isOutOfStock ? 'out-of-stock' : ''}">
          <div class="position-relative">
            <a href="/shop/${product._id}" class="card-link">
              <img
                src="${product.images.main}"
                class="card-img-top img-fluid"
                style="height: 200px; object-fit: contain"
                alt="${product.name}"
              />
            </a>
          </div>
          <div class="card-body">
            <h5 class="card-title text-truncate">${product.name}</h5>
            <div class="d-flex align-items-center">
              <h6 class="card-price mb-0">₹${product.price.toFixed(2)}</h6>
            </div>
            <div class="d-flex justify-content-between align-items-center">
              <span class="${product.stock === 0 || product.isOutOfStock ? 'text-danger' : 'text-success'}">
                ${product.stock === 0 || product.isOutOfStock ? 'Out of Stock' : product.stock + ' Available'}
              </span>
            </div>
            <div class="ratings mb-2">
              <div class="text-warning">
                ${stars}
                <small class="text-muted ms-1">(${product.totalRatings || 0})</small>
              </div>
            </div>
          </div>
          <div class="card-footer bg-white border-0">
            <div class="btn-group w-100" role="group">
              <button class="btn btn-dark-purple w-100 ${product.isOutOfStock ? 'disabled' : ''}" onclick="addToCart('${product._id}')">
                Add to Cart
              </button>
              <button class="btn btn-outline-dark-purple w-100>
                <i class="fas fa-heart"></i> Wishlist
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
    resultsContainer.innerHTML += productCard;
  });
}
