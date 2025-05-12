document.addEventListener("DOMContentLoaded", () => {
  const filterDropdown = document.getElementById("filterDropdown");
  const customDateRange = document.getElementById("customDateRange");
  const startDateInput = document.getElementById("startDate");
  const endDateInput = document.getElementById("endDate");
  const applyButton = customDateRange.querySelector("button");

  let tableData;
  let summaryData;

  // Function to render sales report data into the table
  const renderTable = (data) => {
    const tbody = document.querySelector("table tbody");
    tbody.innerHTML = ""; // Clear existing table rows

    data.forEach((item) => {
      const row = document.createElement("tr");
      row.innerHTML = ` 
        <td>${item.date}</td>
        <td>₹${item.totalSalesRevenue.toFixed(2)}</td>
        <td>₹${item.discountApplied.toFixed(2)}</td>
        <td>₹${item.netSales.toFixed(2)}</td>
        <td>${item.numberOfOrders}</td>
        <td>${item.totalItemsSold}</td>
      `;
      tbody.appendChild(row);
    });
  };

  // Function to update the summary information
  const updateSummary = (summary) => {
    document.querySelector(
      "#totalSalesCount"
    ).textContent = `${summary.totalSalesCount} Orders`;
    document.querySelector(
      "#overallOrderAmount"
    ).textContent = `₹${summary.overallOrderAmount.toFixed(2)}`;
    document.querySelector(
      "#overallDiscount"
    ).textContent = `₹${summary.overallDiscount.toFixed(2)}`;
    summaryData = summary; // Store summary data for PDF generation
  };

  // Function to fetch sales report
  const fetchSalesReport = async (filter, startDate = "", endDate = "") => {
    try {
      const response = await fetch("/admin/sales-report", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ filter, startDate, endDate }),
      });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const data = await response.json();

      if (data.success) {
        tableData = data.data;
        renderTable(data.data); // Render sales report data in the table
        updateSummary(data.summary); // Update summary information
      } else {
        console.error("Error fetching sales report:", data.message);
      }
    } catch (error) {
      console.error("Error:", error);
    }
  };

  // Event listener for dropdown items
  document.querySelectorAll(".dropdown-item").forEach((item) => {
    item.addEventListener("click", function () {
      const selectedFilter = this.getAttribute("data-value");
      filterDropdown.textContent = selectedFilter;

      if (selectedFilter === "Custom Date Range") {
        customDateRange.classList.remove("d-none");
        customDateRange.classList.add("d-flex");
      } else {
        customDateRange.classList.add("d-none");
        customDateRange.classList.remove("d-flex");

        fetchSalesReport(selectedFilter);
      }
    });
  });

  // Event listener for Apply button
  applyButton.addEventListener("click", () => {
    const startDate = startDateInput.value;
    const endDate = endDateInput.value;

    if (startDate && endDate) {
      fetchSalesReport("Custom Date Range", startDate, endDate);
    } else {
      alert("Please select both start and end dates.");
    }
  });

  // Function to format currency
  const formatCurrency = (amount) => `₹${parseFloat(amount).toFixed(2)}`;

  // Function to generate PDF
  const pdfButton = document.querySelector("#pdfDownload");
  pdfButton.addEventListener("click", () => {
    if (!tableData || tableData.length === 0) {
      Swal.fire({
        icon: 'warning',
        title: 'No Data',
        text: 'There is no data to download'
      });
      return;
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    // Set document properties
    doc.setProperties({
      title: 'Sales Report',
      subject: 'Sales Report from PEAKPIX',
      author: 'PEAKPIX',
      creator: 'PEAKPIX Sales System'
    });

    // Company Logo and Header
    doc.setFontSize(24);
    doc.setTextColor(0, 0, 0);
    doc.text("PEAKPIX", 105, 20, { align: "center" });

    // Report Title and Metadata
    doc.setFontSize(16);
    doc.text("Sales Report", 105, 30, { align: "center" });
    
    // Report Details
    doc.setFontSize(10);
    doc.setTextColor(100);
    const reportDate = new Date().toLocaleString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
    doc.text(`Generated on: ${reportDate}`, 105, 38, { align: "center" });
    doc.text(`Report Type: ${filterDropdown.textContent}`, 105, 44, { align: "center" });

    if (filterDropdown.textContent === "Custom Date Range") {
      doc.text(`Period: ${startDateInput.value} to ${endDateInput.value}`, 105, 50, { align: "center" });
    }

    // Sales Data Table
    const tableHeaders = [
      [
        { content: 'Date', styles: { halign: 'center', fontStyle: 'bold' } },
        { content: 'Revenue (₹)', styles: { halign: 'right', fontStyle: 'bold' } },
        { content: 'Discount (₹)', styles: { halign: 'right', fontStyle: 'bold' } },
        { content: 'Net Sales (₹)', styles: { halign: 'right', fontStyle: 'bold' } },
        { content: 'Orders', styles: { halign: 'center', fontStyle: 'bold' } },
        { content: 'Items', styles: { halign: 'center', fontStyle: 'bold' } }
      ]
    ];

    const tableBody = tableData.map(item => [
      { content: item.date, styles: { halign: 'center' } },
      { content: item.totalSalesRevenue.toFixed(2), styles: { halign: 'right' } },
      { content: item.discountApplied.toFixed(2), styles: { halign: 'right' } },
      { content: item.netSales.toFixed(2), styles: { halign: 'right' } },
      { content: item.numberOfOrders, styles: { halign: 'center' } },
      { content: item.totalItemsSold, styles: { halign: 'center' } }
    ]);

    // Generate table with styling
    doc.autoTable({
      head: tableHeaders,
      body: tableBody,
      startY: filterDropdown.textContent === "Custom Date Range" ? 55 : 50,
      theme: 'grid',
      headStyles: {
        fillColor: [51, 51, 51],
        textColor: 255,
        fontSize: 10,
        fontStyle: 'bold',
        lineWidth: 0.1,
        cellPadding: 5
      },
      bodyStyles: {
        fontSize: 9,
        lineColor: [200, 200, 200],
        lineWidth: 0.1,
        cellPadding: 5
      },
      alternateRowStyles: {
        fillColor: [245, 245, 245]
      },
      margin: { top: 60 }
    });

    // Summary Section
    const finalY = doc.autoTable.previous.finalY + 15;
    
    // Summary Box
    doc.setFillColor(240, 240, 240);
    doc.setDrawColor(200, 200, 200);
    doc.rect(14, finalY, 182, 50, 'FD');

    // Summary Title
    doc.setFontSize(12);
    doc.setTextColor(51, 51, 51);
    doc.text("SUMMARY", 105, finalY + 10, { align: "center" });

    // Summary Content
    doc.setFontSize(10);
    const leftCol = 24;
    const rightCol = 120;
    const summaryY = finalY + 20;

    // Format currency
    const formatCurrency = num => `₹ ${num.toFixed(2)}`;

    // Left Column
    doc.text("Total Orders:", leftCol, summaryY);
    doc.text("Total Items Sold:", leftCol, summaryY + 10);

    // Right Column
    doc.text("Total Revenue:", rightCol, summaryY);
    doc.text("Total Discount:", rightCol, summaryY + 10);
    doc.text("Net Revenue:", rightCol, summaryY + 20);

    // Values (Bold)
    doc.setFont(undefined, 'bold');
    doc.text(summaryData.totalSalesCount.toString(), leftCol + 50, summaryY);
    doc.text(tableData.reduce((sum, item) => sum + item.totalItemsSold, 0).toString(), leftCol + 50, summaryY + 10);
    
    doc.text(formatCurrency(summaryData.overallOrderAmount), rightCol + 50, summaryY);
    doc.text(formatCurrency(summaryData.overallDiscount), rightCol + 50, summaryY + 10);
    doc.text(formatCurrency(summaryData.overallOrderAmount - summaryData.overallDiscount), rightCol + 50, summaryY + 20);

    // Footer
    doc.setFontSize(8);
    doc.setTextColor(150);
    doc.text(
      "© PEAKPIX - Generated by Sales Management System",
      105,
      doc.internal.pageSize.height - 10,
      { align: "center" }
    );

    // Save PDF
    doc.save(`PEAKPIX_Sales_Report_${new Date().toISOString().split('T')[0]}.pdf`);
  });

  // Function to generate Excel
  const excelButton = document.querySelector("#excelDownload");
  excelButton.addEventListener("click", () => {
    if (!tableData || tableData.length === 0) {
      Swal.fire({
        icon: 'warning',
        title: 'No Data',
        text: 'There is no data to download'
      });
      return;
    }

    const wb = XLSX.utils.book_new();
    
    // Header Information
    const wsInfo = [
      ["PEAKPIX"],
      ["SALES REPORT"],
      [""],
      [`Report Generated: ${new Date().toLocaleString()}`],
      [`Report Type: ${filterDropdown.textContent}`]
    ];

    if (filterDropdown.textContent === "Custom Date Range") {
      wsInfo.push([`Period: ${startDateInput.value} to ${endDateInput.value}`]);
    }
    wsInfo.push([""]); // Empty row for spacing

    // Table Headers
    const headers = [
      "Date",
      "Total Revenue (₹)",
      "Discount (₹)",
      "Net Sales (₹)",
      "Orders",
      "Items Sold"
    ];
    wsInfo.push(headers);

    // Format Data
    const excelData = tableData.map(item => [
      item.date,
      Number(item.totalSalesRevenue.toFixed(2)),
      Number(item.discountApplied.toFixed(2)),
      Number(item.netSales.toFixed(2)),
      item.numberOfOrders,
      item.totalItemsSold
    ]);

    // Combine all data
    const wsData = [
      ...wsInfo,
      ...excelData,
      [], // Empty row before summary
      ["SUMMARY"],
      [""],
      ["Total Orders:", summaryData.totalSalesCount],
      ["Total Items:", tableData.reduce((sum, item) => sum + item.totalItemsSold, 0)],
      ["Total Revenue (₹):", Number(summaryData.overallOrderAmount.toFixed(2))],
      ["Total Discount (₹):", Number(summaryData.overallDiscount.toFixed(2))],
      ["Net Revenue (₹):", Number((summaryData.overallOrderAmount - summaryData.overallDiscount).toFixed(2))]
    ];

    // Create worksheet
    const ws = XLSX.utils.aoa_to_sheet(wsData);

    // Styling
    ws['!cols'] = [
      { wch: 15 }, // Date
      { wch: 15 }, // Revenue
      { wch: 15 }, // Discount
      { wch: 15 }, // Net Sales
      { wch: 10 }, // Orders
      { wch: 10 }  // Items
    ];

    // Add worksheet to workbook
    XLSX.utils.book_append_sheet(wb, ws, "Sales Report");

    // Save Excel file
    XLSX.writeFile(wb, `PEAKPIX_Sales_Report_${new Date().toISOString().split('T')[0]}.xlsx`);
  });
});
