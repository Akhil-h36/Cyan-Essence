document.addEventListener("DOMContentLoaded", () => {
  // References to DOM elements
  const chartFilterDropdown = document.getElementById("chartFilterDropdown");
  const chartFilterItems = document.querySelectorAll(
    "#chartFilterDropdown + .dropdown-menu .dropdown-item"
  );
  const customDateRangeDiv = document.getElementById("customDateRange");
  const applyButton = document.querySelector("#customDateRange button");
  const startDateInput = document.getElementById("startDate");
  const endDateInput = document.getElementById("endDate");

  let selectedFilter = "Monthly"; // Default filter
  let salesChart; // Chart.js instance

  // Function to fetch sales data and render the chart
  function fetchSalesDataAndRenderChart(
    filter,
    startDate = null,
    endDate = null
  ) {
    let url = `/admin/sales-data?filter=${filter}`;
    if (startDate && endDate) {
      url += `&startDate=${startDate}&endDate=${endDate}`;
    }

    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        updateChart(data);
      })
      .catch((error) => {
        console.error("Error fetching sales data:", error);
      });
  }

  // Function to update the chart
  function updateChart(data) {
    const ctx = document.getElementById("salesChart").getContext("2d");

    if (salesChart) {
      salesChart.destroy(); // Destroy previous chart instance
    }

    salesChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [
          {
            label: "Total Sales",
            data: data.values,
            backgroundColor: "rgba(75, 192, 192, 0.2)", // Bar color
            borderColor: "rgba(75, 192, 192, 1)", // Bar border color
            borderWidth: 1,
          },
        ],
      },
      options: {
        scales: {
          y: {
            beginAtZero: true,
          },
        },
      },
    });
  }

  // Event listeners for filter dropdown items
  chartFilterItems.forEach((item) => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const filterValue = item.getAttribute("data-value");

      // Update dropdown button text
      chartFilterDropdown.textContent = filterValue;

      // Update selected filter
      selectedFilter = filterValue;

      if (selectedFilter === "Custom Date Range") {
        // Show custom date range inputs
        customDateRangeDiv.classList.remove("d-none");
      } else {
        // Hide custom date range inputs
        customDateRangeDiv.classList.add("d-none");

        // Fetch data and update chart
        fetchSalesDataAndRenderChart(selectedFilter);
      }
    });
  });

  // Event listener for 'Apply' button in custom date range
  applyButton.addEventListener("click", () => {
    const startDate = startDateInput.value;
    const endDate = endDateInput.value;

    if (!startDate || !endDate) {
      alert("Please select both start date and end date");
      return;
    }

    // Fetch data with custom date range
    fetchSalesDataAndRenderChart(selectedFilter, startDate, endDate);
  });

  // Initial fetch and render
  fetchSalesDataAndRenderChart(selectedFilter);
});

fetch("/admin/best-sellers")
  .then((response) => response.json())
  .then((data) => {
    const { topProducts, topCategories } = data;

    // Populate best selling products
    const productsContainer = document.getElementById("bestSellingProducts");
    topProducts.forEach((product, index) => {
      const productRow = `
          <tr>
            <td>#${index + 1}</td>
            <td><img src="${product.image}" class="img-fluid" style="width: 40px; height: 40px;" alt="${product.name}" /></td>
            <td>${product.name}</td>
            <td>${product.popularity}</td>
          </tr>`;
        productsContainer.innerHTML += productRow;
    });

    // Populate best selling categories
    const categoriesContainer = document.getElementById(
      "bestSellingCategories"
    );
    topCategories.forEach((category, index) => {
      const categoryRow = `
        <tr>
          <td>#${index + 1}</td>
          <td>${category.name}</td>
          <td>${category.popularity}</td>
        </tr>`;
      categoriesContainer.innerHTML += categoryRow;
    });
  })
  .catch((error) => console.error("Error fetching best sellers:", error));

