const slider = document.getElementById("price-slider");
const minPriceValue = document.getElementById("minPriceValue");
const maxPriceValue = document.getElementById("maxPriceValue");
const minPriceInput = document.getElementById("minPrice");
const maxPriceInput = document.getElementById("maxPrice");

// Get initial values from the data attributes
const sliderConfig = document.getElementById('slider-config');
const initialMinPrice = parseFloat(sliderConfig.getAttribute('data-min-price')) || 200;
const initialMaxPrice = parseFloat(sliderConfig.getAttribute('data-max-price')) || 5000;

noUiSlider.create(slider, {
  start: [initialMinPrice, initialMaxPrice], // Initial values
  connect: true,
  range: {
    min: 200, // Adjust according to your minimum price
    max: 10000, // Adjust according to your maximum price
  },
  format: {
    to: function (value) {
      return `₹${Math.round(value)}`;
    },
    from: function (value) {
      return Number(value.replace("₹", ""));
    },
  },
});

slider.noUiSlider.on("update", function (values, handle) {
  if (handle === 0) {
    minPriceValue.innerHTML = values[0];
    minPriceInput.value = values[0].replace("₹", ""); // Update hidden input
  } else {
    maxPriceValue.innerHTML = values[1];
    maxPriceInput.value = values[1].replace("₹", ""); // Update hidden input
  }
});

// Initialize displayed values with the initial slider values
minPriceValue.innerHTML = slider.noUiSlider.get()[0];
maxPriceValue.innerHTML = slider.noUiSlider.get()[1];
minPriceInput.value = slider.noUiSlider.get()[0].replace("₹", "");
maxPriceInput.value = slider.noUiSlider.get()[1].replace("₹", "");

function previewImage(event, previewId) {
  const reader = new FileReader();
  reader.onload = function () {
    const output = document.getElementById(previewId);
    output.src = reader.result;
    output.style.display = "block";
  };
  reader.readAsDataURL(event.target.files[0]);
}

function updateMainImage(src) {
  document.getElementById("mainImage").src = src;
}
