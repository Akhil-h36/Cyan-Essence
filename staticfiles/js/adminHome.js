const getCsrfToken = () => {
  const cookies = document.cookie.split(';');
  for (let i = 0; i < cookies.length; i++) {
    const cookie = cookies[i].trim();
    if (cookie.startsWith('csrftoken=')) {
      return cookie.substring('csrftoken='.length, cookie.length);
    }
  }
  return '';
};

document.addEventListener("DOMContentLoaded", () => {
  // Initialize elements with null checks
  const filterDropdown = document.getElementById("filterDropdown");
  const customDateRange = document.getElementById("customDateRange");
  const startDateInput = document.getElementById("startDate");
  const endDateInput = document.getElementById("endDate");
  const applyButton = customDateRange?.querySelector("button");
  const dailyDateInput = document.getElementById("dailyDate");
  const dailyDateContainer = document.getElementById("dailyDateContainer");
  const reportResults = document.getElementById("reportResults");
  const pdfButton = document.getElementById("pdfDownload");
  const excelButton = document.getElementById("excelDownload");

  let tableData = [];
  let summaryData = {
    totalSalesCount: 0,
    overallOrderAmount: 0,
    overallDiscount: 0
  }; // Initialize with default values

  // Initialize date inputs
  const initializeDateInputs = () => {
    const today = new Date();
    
    if (startDateInput) {
      startDateInput.valueAsDate = new Date(today.getFullYear(), today.getMonth(), 1);
    }
    
    if (endDateInput) {
      endDateInput.valueAsDate = today;
    }
    
    if (dailyDateInput) {
      dailyDateInput.valueAsDate = today;
    }
  };

  initializeDateInputs();

  // Function to render sales report data
  const renderTable = (data) => {
    const tbody = document.querySelector("table tbody");
    if (!tbody) return;

    tbody.innerHTML = "";

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

  // Function to fetch and display detailed orders for a specific date
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
        <div class="orders-co" style="max-height: 70vh; overflow-y: auto;">
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
        </div>
        <div class="items-co" style="max-height: 50vh; overflow-y: auto;">
          ${itemsHtml}
        </div>
      `,
      width: '800px',
      showCloseButton: true,
      showConfirmButton: false
    });
  };

  // Helper function to get badge class for order status
  const getStatusClass = (status) => {
    switch (status) {
      case 'PENDING': return 'bg-warning text-dark';
      case 'PROCESSING': return 'bg-info text-dark';
      case 'SHIPPED': return 'bg-primary';
      case 'DELIVERED': return 'bg-success';
      case 'CANCELLED': return 'bg-danger';
      default: return 'bg-secondary';
    }
  };

  // Helper function to get badge class for payment status
  const getPaymentStatusClass = (status) => {
    switch (status) {
      case 'PAID': return 'bg-success';
      case 'PENDING': return 'bg-warning text-dark';
      case 'FAILED': return 'bg-danger';
      case 'REFUNDED': return 'bg-info';
      default: return 'bg-secondary';
    }
  };

  // Function to update the summary information
  const updateSummary = (summary) => {
    const totalSalesCount = document.getElementById("totalSalesCount");
    const overallOrderAmount = document.getElementById("overallOrderAmount");
    const overallDiscount = document.getElementById("overallDiscount");
    
    if (totalSalesCount) totalSalesCount.textContent = `${summary.totalSalesCount} Orders`;
    if (overallOrderAmount) overallOrderAmount.textContent = summary.overallOrderAmount.toFixed(2);
    if (overallDiscount) overallDiscount.textContent = summary.overallDiscount.toFixed(2);
    
    // Update the global summaryData
    summaryData = summary;
  };

  // Function to fetch sales report
  const fetchSalesReport = async (filter, startDate = "", endDate = "", specificDate = "") => {
    try {
      if (reportResults) {
        reportResults.innerHTML = '<div class="text-center my-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
      }
      
      const requestBody = { filter };
      
      if (filter === "Custom Date Range") {
        requestBody.startDate = startDate;
        requestBody.endDate = endDate;
      } else if (filter === "Daily" && specificDate) {
        requestBody.specificDate = specificDate;
      }

      console.log("Request body:", requestBody); // Debug log
      
      const response = await fetch("/adminapp/admin/sales-report", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken()
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) throw new Error("Network response was not ok");

      const data = await response.json();
      console.log("Response data:", data); // Debug log

      if (data.success) {
        tableData = data.data;
        renderTable(data.data);
        updateSummary(data.summary);
        
        if (reportResults) {
          reportResults.classList.remove('d-none');
        }
      } else {
        Swal.fire({
          icon: 'error',
          title: 'Error',
          text: data.message || 'Failed to fetch sales report'
        });
      }
    } catch (error) {
      console.error("Error:", error);
      Swal.fire({
        icon: 'error',
        title: 'Error',
        text: 'Failed to fetch sales report'
      });
    }
  };

  // Event listener for dropdown items
  document.querySelectorAll(".dropdown-item").forEach((item) => {
    item.addEventListener("click", function () {
      const selectedFilter = this.getAttribute("data-value");
      if (filterDropdown) {
        filterDropdown.textContent = selectedFilter;
        filterDropdown.setAttribute('data-selected', selectedFilter);
      }

      // Show/hide appropriate date inputs based on filter
      if (selectedFilter === "Custom Date Range") {
        if (customDateRange) {
          customDateRange.classList.remove("d-none");
          customDateRange.classList.add("d-flex");
        }
        if (dailyDateContainer) {
          dailyDateContainer.classList.add("d-none");
        }
      } else if (selectedFilter === "Daily") {
        if (customDateRange) {
          customDateRange.classList.add("d-none");
          customDateRange.classList.remove("d-flex");
        }
        if (dailyDateContainer) {
          dailyDateContainer.classList.remove("d-none");
        }
        // When selecting Daily, fetch using today's date as default
        const today = new Date().toISOString().split('T')[0];
        if (dailyDateInput) {
          dailyDateInput.value = today;
        }
        fetchSalesReport(selectedFilter, "", "", today);
      } else {
        if (customDateRange) {
          customDateRange.classList.add("d-none");
          customDateRange.classList.remove("d-flex");
        }
        if (dailyDateContainer) {
          dailyDateContainer.classList.add("d-none");
        }
        fetchSalesReport(selectedFilter);
      }
    });
  });

  // Event listener for Apply button in custom date range
  if (applyButton) {
    applyButton.addEventListener("click", () => {
      const startDate = startDateInput?.value;
      const endDate = endDateInput?.value;

      if (startDate && endDate) {
        fetchSalesReport("Custom Date Range", startDate, endDate);
      } else {
        Swal.fire({
          icon: 'warning',
          title: 'Missing Dates',
          text: 'Please select both start and end dates.'
        });
      }
    });
  }

  // Event listener for the Daily Date selector
  if (dailyDateInput) {
    dailyDateInput.addEventListener("change", function() {
      const specificDate = this.value;
      if (specificDate) {
        fetchSalesReport("Daily", "", "", specificDate);
      }
    });
  }

  // Function to generate PDF
  // Function to generate enhanced PDF with better styling
  if (pdfButton) {
    pdfButton.addEventListener("click", () => {
      if (!tableData || tableData.length === 0) {
        Swal.fire({
          icon: 'warning',
          title: 'No Data',
          text: 'There is no data to download'
        });
        return;
      }

      try {
        // Initialize jsPDF
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF({
          orientation: 'portrait',
          unit: 'mm',
          format: 'a4'
        });

        // Add autoTable plugin
        if (window.jspdf.jsPDF.API.autoTable) {
          // Get the selected filter and date info
          const selectedFilter = filterDropdown?.getAttribute('data-selected') || filterDropdown?.textContent || 'Daily';
          let dateInfo = '';
          
          if (selectedFilter === "Custom Date Range") {
            dateInfo = `${startDateInput?.value} to ${endDateInput?.value}`;
          } else if (selectedFilter === "Daily" && dailyDateInput?.value) {
            dateInfo = dailyDateInput.value;
          }

          // Set theme colors
          const primaryColor = [41, 128, 185]; //rgb(25, 154, 133)
          const secondaryColor = [52, 73, 94]; //rgb(7, 151, 74)
          const lightGray = [245, 245, 245]; // #f5f5f5
          const mediumGray = [189, 195, 199]; // #bdc3c7

          // Document properties
          doc.setProperties({
            title: `Sales Report - ${selectedFilter}`,
            subject: `Sales Report for ${dateInfo}`,
            author: 'Admin System',
            keywords: 'sales, report, admin',
            creator: 'Sales Report System'
          });

          // Add company header
          const pageWidth = doc.internal.pageSize.getWidth();
          const pageHeight = doc.internal.pageSize.getHeight();
          
          // Header background
          doc.setFillColor(...primaryColor);
          doc.rect(0, 0, pageWidth, 35, 'F');
          
          // Add company name and title
          doc.setFontSize(22);
          doc.setTextColor(255, 255, 255);
          doc.setFont("helvetica", "bold");
          doc.text("Cyan Essence", 45, 20);
          
          doc.setFontSize(14);
          doc.setFont("helvetica", "normal");
          doc.text("Sales Report", 45, 28);
          
          // Add report period banner
          doc.setFillColor(...secondaryColor);
          doc.rect(0, 35, pageWidth, 15, 'F');
          
          doc.setFontSize(11);
          doc.setTextColor(255, 255, 255);
          doc.setFont("helvetica", "bold");
          doc.text(`Report Type: ${selectedFilter}`, pageWidth / 2, 43, { align: 'left' });
          
          if (dateInfo) {
            doc.text(`Period: ${dateInfo}`, pageWidth / 2, 43, { align: 'center' });
          }
          
          // Current date
          const today = new Date().toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          });
          doc.setFontSize(9);
          doc.setTextColor(255, 255, 255);
          doc.text(`Generated on: ${today}`, pageWidth - 15, 43, { align: 'right' });

          // Summary section
          const summaryY = 60;
          
          // Summary title bar
          doc.setFillColor(...secondaryColor);
          doc.rect(15, summaryY, pageWidth - 30, 10, 'F');
          
          doc.setFontSize(12);
          doc.setTextColor(255, 255, 255);
          doc.setFont("helvetica", "bold");
          doc.text("SALES SUMMARY", 20, summaryY + 7);
          
          // Summary content background
          doc.setFillColor(...lightGray);
          doc.rect(15, summaryY + 10, pageWidth - 30, 25, 'F');
          
          // Summary info
          const totalSalesCount = summaryData.totalSalesCount !== undefined ? summaryData.totalSalesCount : 0;
          const overallOrderAmount = summaryData.overallOrderAmount !== undefined ? summaryData.overallOrderAmount.toFixed(2) : '0.00';
          const overallDiscount = summaryData.overallDiscount !== undefined ? summaryData.overallDiscount.toFixed(2) : '0.00';
          const netAmount = (summaryData.overallOrderAmount - summaryData.overallDiscount).toFixed(2);
          
          // Box dividers
          doc.setDrawColor(...mediumGray);
          doc.line(pageWidth/2 - 30, summaryY + 15, pageWidth/2 - 30, summaryY + 30);
          doc.line(pageWidth/2 + 30, summaryY + 15, pageWidth/2 + 30, summaryY + 30);
          
          // Summary value icons/circles
          const summaryIconY = summaryY + 18;
          const iconRadius = 3;
          
          // Icon 1 - Orders
          doc.setFillColor(...primaryColor);
          doc.circle(25, summaryIconY, iconRadius, 'F');
          
          // Icon 2 - Revenue
          doc.circle(pageWidth/2 - 20, summaryIconY, iconRadius, 'F');
          
          // Icon 3 - Discount
          doc.circle(pageWidth/2 + 40, summaryIconY, iconRadius, 'F');
          
          // Summary values
          doc.setFontSize(14);
          doc.setTextColor(0, 0, 0);
          doc.setFont("helvetica", "bold");
          
          // Orders count
          doc.text(`${totalSalesCount}`, 32, summaryIconY + 1);
          doc.setFontSize(9);
          doc.setFont("helvetica", "normal");
          doc.text("Total Orders", 32, summaryIconY + 8);
          
          // Revenue
          doc.setFontSize(14);
          doc.setFont("helvetica", "bold");
          doc.text(`₹${overallOrderAmount}`, pageWidth/2 - 13, summaryIconY + 1);
          doc.setFontSize(9);
          doc.setFont("helvetica", "normal");
          doc.text("Total Revenue", pageWidth/2 - 13, summaryIconY + 8);
          
          // Discount
          doc.setFontSize(14);
          doc.setFont("helvetica", "bold");
          doc.text(`₹${overallDiscount}`, pageWidth/2 + 47, summaryIconY + 1);
          doc.setFontSize(9);
          doc.setFont("helvetica", "normal");
          doc.text("Total Discount", pageWidth/2 + 47, summaryIconY + 8);
          
          // Net Amount (rightmost)
          doc.setFontSize(14);
          doc.setFont("helvetica", "bold");
          doc.text(`₹${netAmount}`, pageWidth - 35, summaryIconY + 1);
          doc.setFontSize(9);
          doc.setFont("helvetica", "normal");
          doc.text("Net Amount", pageWidth - 35, summaryIconY + 8);
          
          // Data visualization - Simple horizontal bar for Orders vs Revenue
          const chartY = summaryY + 45;
          
          // Chart title bar
          doc.setFillColor(...secondaryColor);
          doc.rect(15, chartY, pageWidth - 30, 10, 'F');
          
          doc.setFontSize(12);
          doc.setTextColor(255, 255, 255);
          doc.setFont("helvetica", "bold");
          doc.text("SALES TREND", 20, chartY + 7);
          
          // Chart background
          doc.setFillColor(...lightGray);
          doc.rect(15, chartY + 10, pageWidth - 30, 40, 'F');
          
          // Simple chart - sales distribution (if we have data)
          if (tableData.length > 0) {
            const chartStartX = 25;
            const chartWidth = pageWidth - 50;
            const barHeight = 5;
            const barGap = 8;
            const maxSales = Math.max(...tableData.map(item => item.totalSalesRevenue));
            
            // Just show up to 4 entries to keep it neat
            const chartData = tableData.slice(0, 4);
            
            doc.setFontSize(8);
            doc.setTextColor(0, 0, 0);
            
            chartData.forEach((item, index) => {
              const y = chartY + 20 + (index * barGap);
              const barWidth = (item.totalSalesRevenue / maxSales) * (chartWidth - 50);
              
              // Draw label
              doc.setFont("helvetica", "normal");
              doc.text(item.date, chartStartX, y + 2);
              
              // Draw bar background
              doc.setFillColor(230, 230, 230);
              doc.rect(chartStartX + 45, y, chartWidth - 50, barHeight, 'F');
              
              // Draw actual bar
              doc.setFillColor(...primaryColor);
              doc.rect(chartStartX + 45, y, barWidth, barHeight, 'F');
              
              // Value at end of bar
              doc.setFont("helvetica", "bold");
              doc.text(`₹${item.totalSalesRevenue.toFixed(2)}`, chartStartX + 45 + barWidth + 5, y + 4);
            });
          }
          
          // Table data
          const tableY = chartY + 60;
          
          // Table headers and data
          const headers = [
            { header: 'Date', dataKey: 'date' },
            { header: 'Revenue', dataKey: 'revenue' }, 
            { header: 'Discounts', dataKey: 'discount' },
            { header: 'Net Sales', dataKey: 'net' },
            { header: 'Orders', dataKey: 'orders' },
            { header: 'Items', dataKey: 'items' }
          ];
          
          const tableDataFormatted = tableData.map(item => ({
            date: item.date,
            revenue: `₹${item.totalSalesRevenue.toFixed(2)}`,
            discount: `₹${item.discountApplied.toFixed(2)}`,
            net: `₹${item.netSales.toFixed(2)}`,
            orders: item.numberOfOrders,
            items: item.totalItemsSold
          }));
          
          // Generate table with autotable
          doc.autoTable({
            startY: tableY,
            head: [headers.map(h => h.header)],
            body: tableDataFormatted.map(item => [
              item.date,
              item.revenue,
              item.discount,
              item.net,
              item.orders,
              item.items
            ]),
            headStyles: {
              fillColor: secondaryColor,
              textColor: [255, 255, 255],
              fontStyle: 'bold',
              halign: 'center'
            },
            columnStyles: {
              0: { halign: 'left' },
              1: { halign: 'right' },
              2: { halign: 'right' },
              3: { halign: 'right' },
              4: { halign: 'center' },
              5: { halign: 'center' }
            },
            alternateRowStyles: {
              fillColor: [245, 245, 245]
            },
            margin: { top: 15, right: 15, bottom: 15, left: 15 },
            styles: {
              font: 'helvetica',
              overflow: 'linebreak',
              cellPadding: 4,
            },
            didDrawPage: function(data) {
              // Footer with page number on each page
              const pageNumber = doc.internal.getNumberOfPages();
              doc.setFontSize(8);
              doc.setTextColor(128, 128, 128);
              doc.text(
                `Page ${pageNumber} of ${doc.internal.getNumberOfPages()}`, 
                pageWidth / 2, 
                pageHeight - 10, 
                { align: 'center' }
              );
              
              // Add footnote
              doc.setFontSize(8);
              doc.setTextColor(128, 128, 128);
              doc.text(
                'This report is auto-generated and may contain preliminary data subject to verification.', 
                15, 
                pageHeight - 10
              );
            }
          });
          
          // Save PDF with a meaningfully named file
          let reportPeriod = selectedFilter.toLowerCase().replace(' ', '_');
          if (dateInfo) {
            reportPeriod += '_' + dateInfo.replace(/\s/g, '').replace(/:/g, '-');
          }
          
          doc.save(`sales_report_${reportPeriod}_${new Date().toISOString().slice(0, 10)}.pdf`);
          
          Swal.fire({
            icon: 'success',
            title: 'Success',
            text: 'PDF report has been generated successfully!',
            timer: 2000,
            showConfirmButton: false
          });
        } else {
          throw new Error("AutoTable plugin not loaded");
        }
      } catch (error) {
        console.error("PDF generation error:", error);
        Swal.fire({
          icon: 'error',
          title: 'PDF Generation Failed',
          text: 'There was an error generating the PDF report: ' + error.message
        });
      }
    });
  }
});