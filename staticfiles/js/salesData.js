// salesData.js - Chart rendering and dynamic data loading
// Add these functions at the top of salesData.js before using them
// Declare tableData variable
let tableData;
let summaryData;

// Function to render sales report data into the table
const renderTable = (data) => {
  const tbody = document.querySelector("table tbody");
  if (!tbody) return; // Check if the table exists on the current page

  tbody.innerHTML = ""; // Clear existing table rows

  data.forEach((item) => {
    const row = document.createElement("tr");
    row.classList.add("report-row");
    row.setAttribute("data-date", item.date);
    row.innerHTML = ` 
      <td>${item.date}</td>
      <td>₹${item.totalSalesRevenue.toFixed(2)}</td>
      <td>₹${item.discountApplied.toFixed(2)}</td>
      <td>₹${item.netSales.toFixed(2)}</td>
      <td>${item.numberOfOrders}</td>
      <td>${item.totalItemsSold}</td>
      <td>
        <button class="btn btn-sm btn-info view-details" data-date="${item.date}">
          <i class="fas fa-eye"></i> Details
        </button>
      </td>
    `;
    tbody.appendChild(row);
  });

  // Add event listeners to the detail buttons
  document.querySelectorAll(".view-details").forEach(button => {
    button.addEventListener("click", function() {
      const date = this.getAttribute("data-date");
      fetchDetailedOrders(date);
    });
  });
};

// Function to fetch detailed orders for a specific date
const fetchDetailedOrders = async (date) => {
  try {
    const response = await fetch("/adminapp/admin/detailed-orders", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken()
      },
      body: JSON.stringify({ date }),
    });

    if (!response.ok) throw new Error("Network response was not ok");

    const data = await response.json();

    if (data.success) {
      showDetailedOrdersModal(date, data.orders);
    } else {
      Swal.fire({
        icon: 'error',
        title: 'Error',
        text: data.message || 'Failed to fetch order details'
      });
    }
  } catch (error) {
    console.error("Error:", error);
    Swal.fire({
      icon: 'error',
      title: 'Error',
      text: 'Failed to fetch order details'
    });
  }
};

// Helper function to get status class for badges
const getStatusClass = (status) => {
  switch (status?.toLowerCase()) {
    case 'completed':
      return 'bg-success';
    case 'processing':
      return 'bg-primary';
    case 'pending':
      return 'bg-warning';
    case 'cancelled':
      return 'bg-danger';
    default:
      return 'bg-secondary';
  }
};

// Helper function to get payment status class for badges
const getPaymentStatusClass = (status) => {
  switch (status?.toLowerCase()) {
    case 'paid':
      return 'bg-success';
    case 'pending':
      return 'bg-warning';
    case 'failed':
      return 'bg-danger';
    case 'refunded':
      return 'bg-info';
    default:
      return 'bg-secondary';
  }
};

// Function to display a modal with detailed orders
const showDetailedOrdersModal = (date, orders) => {
  // Create order list HTML
  let ordersHtml = '';
  
  orders.forEach(order => {
    const statusClass = getStatusClass(order.order_status);
    const paymentStatusClass = getPaymentStatusClass(order.payment_status);
    
    ordersHtml += `
      <div class="card mb-3">
        <div class="card-header d-flex justify-content-between align-items-center">
          <span>Order #${order.id}</span>
          <small>${new Date(order.created_at).toLocaleString()}</small>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <p><strong>Customer:</strong> ${order.user ? order.user.username : 'Guest'}</p>
              <p><strong>Items:</strong> ${order.items_count}</p>
              <p><strong>Payment Method:</strong> ${order.payment_method}</p>
            </div>
            <div class="col-md-6">
              <p><strong>Amount:</strong> ₹${order.total_amount.toFixed(2)}</p>
              <p><strong>Status:</strong> <span class="badge ${statusClass}">${order.order_status}</span></p>
              <p><strong>Payment:</strong> <span class="badge ${paymentStatusClass}">${order.payment_status}</span></p>
              ${order.is_returned ? '<p><span class="badge bg-warning">Returned</span></p>' : ''}
            </div>
          </div>
          <div class="mt-2">
            <button class="btn btn-sm btn-primary view-items" data-order-id="${order.id}">
              View Items
            </button>
          </div>
        </div>
      </div>
    `;
  });
  
  // If no orders, show a message
  if (orders.length === 0) {
    ordersHtml = '<div class="alert alert-info">No orders found for this date.</div>';
  }
  
  // Create and show the modal
  Swal.fire({
    title: `Orders for ${date}`,
    html: `
      <div class="orders-container" style="max-height: 70vh; overflow-y: auto;">
        ${ordersHtml}
      </div>
    `,
    width: '800px',
    showCloseButton: true,
    showConfirmButton: false,
    didOpen: () => {
      // Add event listeners to the "View Items" buttons
      document.querySelectorAll(".view-items").forEach(button => {
        button.addEventListener("click", function() {
          const orderId = this.getAttribute("data-order-id");
          fetchOrderItems(orderId);
        });
      });
    }
  });
};

// Function to fetch order items
const fetchOrderItems = async (orderId) => {
  try {
    const response = await fetch("/adminapp/admin/order-items", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken()
      },
      body: JSON.stringify({ orderId }),
    });

    if (!response.ok) throw new Error("Network response was not ok");

    const data = await response.json();

    if (data.success) {
      showOrderItemsModal(data.order, data.items);
    } else {
      Swal.fire({
        icon: 'error',
        title: 'Error',
        text: data.message || 'Failed to fetch order items'
      });
    }
  } catch (error) {
    console.error("Error:", error);
    Swal.fire({
      icon: 'error',
      title: 'Error',
      text: 'Failed to fetch order items'
    });
  }
};

// Function to display a modal with order items
const showOrderItemsModal = (order, items) => {
  // Create items table HTML
  let itemsHtml = `
    <table class="table table-striped">
      <thead>
        <tr>
          <th>Product</th>
          <th>Variant</th>
          <th>Price</th>
          <th>Quantity</th>
          <th>Total</th>
        </tr>
      </thead>
      <tbody>
  `;
  
  items.forEach(item => {
    itemsHtml += `
      <tr>
        <td>${item.product_name}</td>
        <td>${item.variant || 'N/A'}</td>
        <td>₹${item.price.toFixed(2)}</td>
        <td>${item.quantity}</td>
        <td>₹${(item.price * item.quantity).toFixed(2)}</td>
      </tr>
    `;
  });
  
  itemsHtml += `
      </tbody>
    </table>
  `;
  
  // Create and show the modal
  Swal.fire({
    title: `Order #${order.id} Details`,
    html: `
      <div class="order-info mb-3">
        <div class="row">
          <div class="col-md-6">
            <p><strong>Date:</strong> ${new Date(order.created_at).toLocaleString()}</p>
            <p><strong>Customer:</strong> ${order.user ? order.user.username : 'Guest'}</p>
            <p><strong>Payment Method:</strong> ${order.payment_method}</p>
          </div>
          <div class="col-md-6">
            <p><strong>Subtotal:</strong> ₹${order.subtotal.toFixed(2)}</p>
            <p><strong>Discount:</strong> ₹${order.discount_amount.toFixed(2)}</p>
            <p><strong>Total:</strong> ₹${order.total_amount.toFixed(2)}</p>
          </div>
        </div>
        <div class="status-info">
          <span class="badge ${getStatusClass(order.order_status)}">${order.order_status}</span>
          <span class="badge ${getPaymentStatusClass(order.payment_status)}">${order.payment_status}</span>
          ${order.is_returned ? '<span class="badge bg-warning">Returned</span>' : ''}
        </div>
      </div>
      <div class="items-container">
        <h5>Order Items</h5>
        ${itemsHtml}
      </div>
    `,
    width: '800px',
    showCloseButton: true,
    showConfirmButton: false
  });
};

// Function to update the summary information
const updateSummary = (summary) => {
  const totalSalesCount = document.querySelector("#totalSalesCount");
  const overallOrderAmount = document.querySelector("#overallOrderAmount");
  const overallDiscount = document.querySelector("#overallDiscount");

  if (totalSalesCount) {
    totalSalesCount.textContent = `${summary.totalSalesCount} Orders`;
  }
  if (overallOrderAmount) {
    overallOrderAmount.textContent = `₹${summary.overallOrderAmount.toFixed(2)}`;
  }
  if (overallDiscount) {
    overallDiscount.textContent = `₹${summary.overallDiscount.toFixed(2)}`;
  }
  
  summaryData = summary; // Store summary data for PDF generation
};

// Function to get CSRF token from cookies
const getCsrfToken = () => {
  const name = 'csrftoken';
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
};

// Function to fetch sales report data with filter
const fetchSalesReport = async (filter, startDate = "", endDate = "", specificDate = "") => {
  try {
    const response = await fetch("/adminapp/admin/sales-report", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken()
      },
      body: JSON.stringify({ filter, startDate, endDate, specificDate }),
    });

    if (!response.ok) {
      throw new Error("Network response was not ok");
    }

    const data = await response.json();

    if (data.success) {
      // Save table data for potential export
      tableData = data.data;
      
      // Update table and summary
      renderTable(data.data);
      updateSummary(data.summary);
      
      // Also update chart
      updateChart({
        labels: data.data.map(item => item.date),
        datasets: [
          {
            // Revenue data
            data: data.data.map(item => item.netSales)
          },
          {
            // Orders data
            data: data.data.map(item => item.numberOfOrders)
          }
        ]
      });
      
      return data;
    } else {
      console.error("Error fetching sales report:", data.message);
      Swal.fire({
        icon: 'error',
        title: 'Error',
        text: data.message || 'Failed to fetch sales report'
      });
      return null;
    }
  } catch (error) {
    console.error("Error:", error);
    Swal.fire({
      icon: 'error',
      title: 'Error',
      text: 'Failed to fetch sales report'
    });
    return null;
  }
};

document.addEventListener("DOMContentLoaded", () => {
  // Chart configuration
  let salesChart;
  
  // Initialize Sales Chart
  const initSalesChart = () => {
    const ctx = document.getElementById('salesChart');
    if (!ctx) return; // Check if chart canvas exists on the current page
    
    const ctxObj = ctx.getContext('2d');
    
    salesChart = new Chart(ctxObj, {
      type: 'bar',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Revenue',
            data: [],
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1,
            yAxisID: 'y'
          },
          {
            label: 'Orders',
            data: [],
            backgroundColor: 'rgba(153, 102, 255, 0.2)',
            borderColor: 'rgba(153, 102, 255, 1)',
            borderWidth: 1,
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            title: {
              display: true,
              text: 'Revenue (₹)'
            },
            beginAtZero: true
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            title: {
              display: true,
              text: 'Number of Orders'
            },
            beginAtZero: true,
            grid: {
              drawOnChartArea: false
            }
          }
        }
      }
    });
  };
  
  // Function to update chart with new data
  const updateChart = (chartData) => {
    if (!salesChart) return;
    
    salesChart.data.labels = chartData.labels;
    salesChart.data.datasets[0].data = chartData.datasets[0].data;
    salesChart.data.datasets[1].data = chartData.datasets[1].data;
    salesChart.update();
  };
  
  // Function to fetch and display best selling products
  const fetchBestSellingProducts = async () => {
    try {
      const productsTbody = document.getElementById('bestSellingProducts');
      if (!productsTbody) return; // Check if the element exists on the current page
      
      const response = await fetch("/adminapp/admin/best-selling-products");
      
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      
      const data = await response.json();
      
      if (data.success) {
        productsTbody.innerHTML = '';
        
        data.products.forEach(product => {
          const row = document.createElement('tr');
          
          // Calculate popularity for progress bar (0-100%)
          const popularityPercentage = Math.min(100, (product.total_sold / data.products[0].total_sold) * 100);
          
          row.innerHTML = `
            <td>${product.rank}</td>
            <td>
              <img src="${product.image_url || '/static/images/placeholder.png'}" 
                   alt="${product.name}" class="img-thumbnail" width="50">
            </td>
            <td>${product.name}</td>
            <td>
              <div class="progress">
                <div class="progress-bar bg-success" role="progressbar" 
                     style="width: ${popularityPercentage}%" 
                     aria-valuenow="${popularityPercentage}" 
                     aria-valuemin="0" aria-valuemax="100">
                  ${product.total_sold} units
                </div>
              </div>
            </td>
          `;
          
          productsTbody.appendChild(row);
        });
      }
    } catch (error) {
      console.error("Error fetching best selling products:", error);
    }
  };
  
  // Function to fetch and display best selling categories
  const fetchBestSellingCategories = async () => {
    try {
      const categoriesTbody = document.getElementById('bestSellingCategories');
      if (!categoriesTbody) return; // Check if the element exists on the current page
      
      const response = await fetch("/adminapp/admin/best_selling_categories");
      
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      
      const data = await response.json();
      
      if (data.success) {
        categoriesTbody.innerHTML = '';
        
        data.categories.forEach(category => {
          const row = document.createElement('tr');
          
          // Calculate popularity for progress bar (0-100%)
          const popularityPercentage = Math.min(100, (category.total_sold / data.categories[0].total_sold) * 100);
          
          row.innerHTML = `
            <td>${category.rank}</td>
            <td>${category.name}</td>
            <td>
              <div class="progress">
                <div class="progress-bar bg-info" role="progressbar" 
                     style="width: ${popularityPercentage}%" 
                     aria-valuenow="${popularityPercentage}" 
                     aria-valuemin="0" aria-valuemax="100">
                  ${category.total_sold} units
                </div>
              </div>
            </td>
          `;
          
          categoriesTbody.appendChild(row);
        });
      }
    } catch (error) {
      console.error("Error fetching best selling categories:", error);
    }
  };
  
  // Function to export sales report to PDF
  const exportToPDF = () => {
    if (!tableData || tableData.length === 0) {
      Swal.fire({
        icon: 'warning',
        title: 'No Data',
        text: 'There is no data to export'
      });
      return;
    }
    
    const doc = new jsPDF();
    
    // Add header
    doc.setFontSize(18);
    doc.text("Sales Report", 105, 15, null, null, "center");
    
    // Add filter info
    const filterInfo = document.getElementById("chartFilterDropdown").textContent;
    doc.setFontSize(12);
    doc.text(`Filter: ${filterInfo}`, 105, 25, null, null, "center");
    
    // Add date
    const currentDate = new Date().toLocaleDateString();
    doc.text(`Generated: ${currentDate}`, 105, 30, null, null, "center");
    
    // Add summary info
    if (summaryData) {
      doc.setFontSize(14);
      doc.text("Summary", 14, 40);
      doc.setFontSize(10);
      doc.text(`Total Orders: ${summaryData.totalSalesCount}`, 14, 48);
      doc.text(`Total Revenue: ₹${summaryData.overallOrderAmount.toFixed(2)}`, 14, 54);
      doc.text(`Total Discount: ₹${summaryData.overallDiscount.toFixed(2)}`, 14, 60);
    }
    
    // Add table
    doc.setFontSize(14);
    doc.text("Sales Data", 14, 70);
    
    // Convert table data for autoTable
    const tableHeaders = ["Date", "Revenue", "Discount", "Net Sales", "Orders", "Items"];
    const tableRows = tableData.map(item => [
      item.date, 
      `₹${item.totalSalesRevenue.toFixed(2)}`,
      `₹${item.discountApplied.toFixed(2)}`,
      `₹${item.netSales.toFixed(2)}`,
      item.numberOfOrders,
      item.totalItemsSold
    ]);
    
    doc.autoTable({
      head: [tableHeaders],
      body: tableRows,
      startY: 75,
      styles: { fontSize: 8 }
    });
    
    // Save the PDF
    doc.save("sales-report.pdf");
  };
  
  // Function to export sales report to Excel
  const exportToExcel = () => {
    if (!tableData || tableData.length === 0) {
      Swal.fire({
        icon: 'warning',
        title: 'No Data',
        text: 'There is no data to export'
      });
      return;
    }
    
    // Prepare data for export
    const excelData = tableData.map(item => ({
      Date: item.date,
      "Total Sales Revenue": item.totalSalesRevenue,
      "Discount Applied": item.discountApplied,
      "Net Sales": item.netSales,
      "Number of Orders": item.numberOfOrders,
      "Total Items Sold": item.totalItemsSold
    }));
    
    // Create worksheet
    const ws = XLSX.utils.json_to_sheet(excelData);
    
    // Create workbook
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Sales Report");
    
    // Generate Excel file
    XLSX.writeFile(wb, "sales-report.xlsx");
  };
  
  // Initialize the chart
  initSalesChart();
  
  // Setup event listeners
  // For filter dropdown
  document.querySelectorAll("#chartFilterDropdown + .dropdown-menu .dropdown-item").forEach((item) => {
    item.addEventListener("click", function() {
      const selectedFilter = this.getAttribute("data-value");
      document.getElementById("chartFilterDropdown").textContent = selectedFilter;
      
      // Fetch sales report with the selected filter
      fetchSalesReport(selectedFilter);
    });
  });
  
  // For date pickers
  const startDatePicker = document.getElementById("startDate");
  const endDatePicker = document.getElementById("endDate");
  const applyDateRangeBtn = document.getElementById("applyDateRange");
  
  if (applyDateRangeBtn) {
    applyDateRangeBtn.addEventListener("click", function() {
      const startDate = startDatePicker.value;
      const endDate = endDatePicker.value;
      
      if (startDate && endDate) {
        fetchSalesReport("Custom Date Range", startDate, endDate);
      } else {
        Swal.fire({
          icon: 'warning',
          title: 'Missing Dates',
          text: 'Please select both start and end dates'
        });
      }
    });
  }

  // For daily date filter
  const specificDatePicker = document.getElementById("specificDate");
  const applySpecificDateBtn = document.getElementById("applySpecificDate");
  
  if (applySpecificDateBtn) {
    applySpecificDateBtn.addEventListener("click", function() {
      const specificDate = specificDatePicker.value;
      
      if (specificDate) {
        fetchSalesReport("Daily", "", "", specificDate);
      } else {
        Swal.fire({
          icon: 'warning',
          title: 'Missing Date',
          text: 'Please select a date'
        });
      }
    });
  }
  
  // For export buttons
  const exportPdfBtn = document.getElementById("exportPdf");
  if (exportPdfBtn) {
    exportPdfBtn.addEventListener("click", exportToPDF);
  }
  
  const exportExcelBtn = document.getElementById("exportExcel");
  if (exportExcelBtn) {
    exportExcelBtn.addEventListener("click", exportToExcel);
  }
  
  // Fetch initial data
  fetchSalesReport('Daily');
  fetchBestSellingProducts();
  fetchBestSellingCategories();
});