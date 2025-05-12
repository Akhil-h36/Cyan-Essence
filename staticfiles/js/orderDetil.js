async function cancelOrder(orderId) {
  try {
    const { value: reason } = await Swal.fire({
      title: 'Cancel Order',
      input: 'textarea',
      inputLabel: 'Please provide a reason for cancellation',
      inputPlaceholder: 'Enter your reason here...',
      inputAttributes: {
        'aria-label': 'Cancellation reason'
      },
      showCancelButton: true,
      inputValidator: (value) => {
        if (!value || value.trim().length === 0) {
          return 'You need to provide a reason for cancellation!'
        }
      }
    });

    if (reason) {
      const response = await fetch(`/account/order-history/cancel/${orderId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ reason: reason.trim() }),
      });

      const data = await response.json();

      if (response.ok) {
        await Swal.fire({
          icon: 'success',
          title: 'Success',
          text: 'Order cancelled successfully',
          timer: 1500,
          showConfirmButton: false
        });
        window.location.reload();
      } else {
        Swal.fire({
          icon: 'error',
          title: 'Error',
          text: data.message || 'Failed to cancel order'
        });
      }
    }
  } catch (error) {
    console.error('Error:', error);
    Swal.fire({
      icon: 'error',
      title: 'Error',
      text: 'An error occurred while cancelling the order'
    });
  }
}

async function returnOrder(orderId) {
  try {
    const { value: reason } = await Swal.fire({
      title: 'Return Order',
      input: 'textarea',
      inputLabel: 'Please provide a reason for return',
      inputPlaceholder: 'Enter your reason here...',
      inputAttributes: {
        'aria-label': 'Return reason'
      },
      showCancelButton: true,
      inputValidator: (value) => {
        if (!value || value.trim().length === 0) {
          return 'You need to provide a reason for return!'
        }
      }
    });

    if (reason) {
      const response = await fetch(`/account/order-history/return/${orderId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ reason: reason.trim() }),
      });

      const data = await response.json();

      if (response.ok) {
        await Swal.fire({
          icon: 'success',
          title: 'Success',
          text: 'Return request submitted successfully',
          timer: 1500,
          showConfirmButton: false
        });
        window.location.reload();
      } else {
        Swal.fire({
          icon: 'error',
          title: 'Error',
          text: data.message || 'Failed to submit return request'
        });
      }
    }
  } catch (error) {
    console.error('Error:', error);
    Swal.fire({
      icon: 'error',
      title: 'Error',
      text: 'An error occurred while submitting return request'
    });
  }
}

async function downloadInvoice(orderId) {
  try {
    // Fetch order data to check its status
    const response = await fetch(`/account/order-history/${orderId}/invoice-data`);
    if (!response.ok) throw new Error('Failed to fetch order data');
    const orderData = await response.json();
    console.log('Order Data:', orderData); // For debugging

    // Check if the order status allows invoice download
    const allowedStatuses = ['Delivered', 'Returned', 'Cancelled'];
    if (!allowedStatuses.includes(orderData.status)) {
      return Swal.fire({
        icon: 'warning',
        title: 'Invalid Action',
        text: 'Invoice can only be downloaded for delivered, returned, or cancelled orders.',
      });
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    // Company Header
    doc.setFontSize(28);
    doc.setTextColor(44, 62, 80);
    doc.text("PEAKPIX", 105, 25, { align: "center" });
    
    doc.setFontSize(12);
    doc.setTextColor(100);
    doc.text("Premium Audio Equipment", 105, 35, { align: "center" });
    doc.text("123 Audio Street, Sound City, 12345", 105, 40, { align: "center" });
    doc.text("Phone: +1 234-567-8900 | Email: sales@peakpix.com", 105, 45, { align: "center" });
    
    // Invoice Title
    doc.setFontSize(20);
    doc.setTextColor(0);
    doc.text("INVOICE", 105, 60, { align: "center" });

    // Order Details Box
    doc.setDrawColor(200);
    doc.setFillColor(245, 245, 245);
    doc.roundedRect(14, 70, 182, 45, 3, 3, 'FD');

    // Left Column - Order Details
    doc.setFontSize(10);
    doc.setFont(undefined, 'bold');
    doc.text("Order Details:", 20, 78);
    doc.setFont(undefined, 'normal');
    doc.text(`Order ID: ${orderData.orderId}`, 20, 85);
    doc.text(`Order Date: ${new Date(orderData.dateOrdered).toLocaleDateString()}`, 20, 92);
    doc.text(`Payment Method: ${orderData.paymentMethod}`, 20, 99);
    doc.text(`Order Status: ${orderData.status}`, 20, 106);

    // Right Column - Billing Details
    doc.setFont(undefined, 'bold');
    doc.text("Bill To:", 110, 78);
    doc.setFont(undefined, 'normal');
    doc.text(`${orderData.name}`, 110, 85);
    doc.text(`${orderData.location}`, 110, 92);
    doc.text(`${orderData.city}, ${orderData.state} - ${orderData.zip}`, 110, 99);
    doc.text(`Mobile: ${orderData.mobile}`, 110, 106);

    // Items Table
    const tableHeaders = [
      [
        { content: 'Product', styles: { halign: 'left', fontStyle: 'bold' } },
        { content: 'Qty', styles: { halign: 'center', fontStyle: 'bold' } },
        { content: 'Price', styles: { halign: 'right', fontStyle: 'bold' } },
        { content: 'Total', styles: { halign: 'right', fontStyle: 'bold' } }
      ]
    ];

    // Map order items correctly based on the data structure
    const tableBody = orderData.orderItems.map(item => [
      { content: item.product.name || 'N/A', styles: { halign: 'left' } },
      { content: String(item.quantity || 0), styles: { halign: 'center' } },
      { content: (item.product.price || 0).toFixed(2), styles: { halign: 'right' } },
      { 
        content: ((item.product.price || 0) * (item.quantity || 0)).toFixed(2), 
        styles: { halign: 'right' } 
      }
    ]);

    doc.autoTable({
      head: tableHeaders,
      body: tableBody,
      startY: 125,
      theme: 'grid',
      headStyles: {
        fillColor: [44, 62, 80],
        textColor: 255,
        fontSize: 10,
        fontStyle: 'bold',
        cellPadding: 5
      },
      bodyStyles: {
        fontSize: 9,
        cellPadding: 5
      },
      columnStyles: {
        0: { cellWidth: 90 },
        1: { cellWidth: 25 },
        2: { cellWidth: 35 },
        3: { cellWidth: 35 }
      }
    });

    // Calculate totals correctly
    const subtotal = orderData.orderItems.reduce((sum, item) => 
      sum + ((item.product.price || 0) * (item.quantity || 0)), 0);

    // Summary Box
    const finalY = doc.autoTable.previous.finalY + 10;
    doc.setFillColor(245, 245, 245);
    doc.rect(116, finalY, 80, 50, 'F');

    // Add summary details with proper number formatting
    let currentY = finalY + 10;
    const addSummaryLine = (label, value, bold = false) => {
      doc.setFont(undefined, bold ? 'bold' : 'normal');
      doc.text(label, 120, currentY);
      doc.text(`₹${Number(value).toFixed(2)}`, 185, currentY, { align: 'right' });
      currentY += 8;
    };

    // Use calculated subtotal and ensure all values are numbers
    addSummaryLine('Subtotal:', Number(orderData.totalAmount || 0));
    addSummaryLine('Shipping:', Number(orderData.shippingCharge || 0));
    addSummaryLine('Discount:', Number(orderData.discountApplied || 0));
    doc.line(120, currentY - 4, 196, currentY - 4);
    addSummaryLine('Grand Total:', Number(orderData.finalTotal || subtotal), true);

    // Footer
    const pageHeight = doc.internal.pageSize.height;
    doc.setFontSize(8);
    doc.setTextColor(128);
    doc.text('This is a computer-generated invoice and does not require a signature.', 105, pageHeight - 25, { align: 'center' });
    doc.text('Thank you for shopping with PEAKPIX!', 105, pageHeight - 20, { align: 'center' });

    // Save the PDF
    doc.save(`PEAKPIX_Invoice_${orderId}.pdf`);

  } catch (error) {
    console.error('Error details:', error);
    Swal.fire({
      icon: 'error',
      title: 'Error',
      text: 'Failed to generate invoice: ' + error.message
    });
  }
}