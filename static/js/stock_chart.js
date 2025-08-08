// Chart Data Arrays
let dateData = [];
let closePriceData = [];
let ema30Data = [];
let ema50Data = [];
let ema200Data = [];
let volumeData = [];

// The Stock Chart
let stockChart;

// Colors
const DATE_COLOR = "rgba(100, 100, 100, 1)";
const VOLUME_COLOR = "rgba(78, 140, 255, 0.75)";
const FILL_COLOR = "rgba(255, 255, 255, 1)";
const STROKE_STYLE = "rgba(0,0,0,0.4)";
const POINT_HOVER_COLOR = "rgba(100, 0, 255, 1)";
const TF_TOOLTIP_TEXT_COLOR = "white";

// Limits
const MAX_X_TICKS = 12;
const ZOOM_MIN_RANGE = 5; // minimum number of values to show when zoomed in
const DISPLAY_TOOLTIP_DEFAULT = false; // OFF by default
const CHART_SPINNER_DELAY = 200; // in ms

// Sizing
const VOLUME_AXIS_MAX_MULTIPLIER = 5; // volume bars take (1/multplier) height of the chart
const POINT_HOVER_RADIUS = 7;
const EMA_BORDER_WIDTH = 1.5;
const EMA_POINT_RADIUS = 0;
const X_OFFSET = 10;
const Y_OFFSET = 18;
const BOX_PADDING = 4;
const LINE_DASH = [5, 5];
const LINE_WIDTH = 1;
const LEGEND_CIRCLE_SIZE = 12;

// Font
const LABEL_FONT_SIZE = 12;
const LABEL_FONT_STYLE = "Arial";

// Chart Options
const CHART_BACKGROUND_COLOR = "transparent";
const CHART_TENSION = 0.3;
const CHART_FILL = false;
const CHART_INTERACTION_MODE = "index";
const CHART_INTERACTION_INTERSECT = false;

// Dataset Labels
const DATE_LABEL = "Date";
const CLOSE_PRICE_LABEL = "Close-Price";
const EMA_30_LABEL = "30-EMA";
const EMA_50_LABEL = "50-EMA";
const EMA_200_LABEL = "200-EMA";
const VOLUME_LABEL = "Volume";

// Defaults Texts
const DATA_MISSING_TEXT = "N/A";

let displayTooltip = DISPLAY_TOOLTIP_DEFAULT;
let emaData = undefined; // Boolean value telling whether to show ema data or not

const dateValue = document.getElementById("date-value");
const closePriceValue = document.getElementById("close-price-value");
const ema30Value = document.getElementById("ema-30-value");
const ema50Value = document.getElementById("ema-50-value");
const ema200Value = document.getElementById("ema-200-value");
const volumeValue = document.getElementById("volume-value");

dateValue.style.color = DATE_COLOR;
closePriceValue.style.color = CLOSE_PRICE_COLOR;
ema30Value.style.color = EMA_30_COLOR;
ema50Value.style.color = EMA_50_COLOR;
ema200Value.style.color = EMA_200_COLOR;
volumeValue.style.color = VOLUME_COLOR;

const tooltipToggle = document.getElementById("tooltip-toggle");
tooltipToggle.checked = displayTooltip;
// Handle tooltop toggle event
tooltipToggle.addEventListener("change", function () {
  displayTooltip = tooltipToggle.checked;

  // Dynamically enable/disable tooltip display while keeping its internal state alive
  stockChart.options.plugins.tooltip.enabled = displayTooltip;
  stockChart.update();
});

const tfChangePerc = document.getElementById("tf-change-perc");
const ctx = document.getElementById("stock-chart").getContext("2d");

function updateHoverInfoText(index) {
  let dateVal = DATA_MISSING_TEXT;
  let closePriceVal = DATA_MISSING_TEXT;
  let volumeVal = DATA_MISSING_TEXT;
  let ema30Val = DATA_MISSING_TEXT;
  let ema50Val = DATA_MISSING_TEXT;
  let ema200Val = DATA_MISSING_TEXT;

  if (index !== null) {
    dateVal = dateData.at(index);
    closePriceVal = closePriceData
      .at(index)
      .toFixed(DECIMAL_PRECISION)
      .toLocaleString("en-US");
    volumeVal = volumeData.at(index).toLocaleString("en-US");

    if (emaData) {
      ema30Val = ema30Data
        .at(index)
        .toFixed(DECIMAL_PRECISION)
        .toLocaleString("en-US");
      ema50Val = ema50Data
        .at(index)
        .toFixed(DECIMAL_PRECISION)
        .toLocaleString("en-US");
      ema200Val = ema200Data
        .at(index)
        .toFixed(DECIMAL_PRECISION)
        .toLocaleString("en-US");
    }
  }

  dateValue.textContent = `${DATE_LABEL}: ${dateVal}`;
  closePriceValue.textContent = `${CLOSE_PRICE_LABEL}: ${closePriceVal}`;
  volumeValue.textContent = `${VOLUME_LABEL}: ${volumeVal}`;
  ema30Value.textContent = `${EMA_30_LABEL}: ${ema30Val}`;
  ema50Value.textContent = `${EMA_50_LABEL}: ${ema50Val}`;
  ema200Value.textContent = `${EMA_200_LABEL}: ${ema200Val}`;
}

// Hover Plugin:
// Draw Hover vertical/horizontal dashed lines +
// Update Hover info +
// Display Hover data on the right with colored background +
// Display Hover date on the bottom with colored background
const hoverPlugin = {
  id: "hoverPlugin",
  afterDraw(chart) {
    const { ctx, chartArea, tooltip } = chart;
    ctx.save();
    ctx.setLineDash(LINE_DASH);
    ctx.lineWidth = LINE_WIDTH;
    ctx.font = `${LABEL_FONT_SIZE}px ${LABEL_FONT_STYLE}`;
    ctx.textBaseline = "middle";

    if (tooltip._active && tooltip._active.length) {
      const active = tooltip._active[0];
      const x = active.element.x;
      const y = active.element.y;
      const hoveredIndex = active.index;

      ctx.strokeStyle = STROKE_STYLE;
      // Draw vertical dashed line
      ctx.beginPath();
      ctx.moveTo(x, chartArea.top);
      ctx.lineTo(x, chartArea.bottom);
      ctx.stroke();

      // Draw horizontal dashed line
      ctx.beginPath();
      ctx.moveTo(chartArea.left, y);
      ctx.lineTo(chartArea.right, y);
      ctx.stroke();

      // Update HTML hover info
      updateHoverInfoText(hoveredIndex);

      // Get the dataset values at the hovered index
      const dateVal = dateData[hoveredIndex];
      const closePriceVal =
        closePriceData[hoveredIndex].toFixed(DECIMAL_PRECISION);
      let ema30Val = undefined;
      let ema50Val = undefined;
      let ema200Val = undefined;
      if (emaData) {
        ema30Val = ema30Data[hoveredIndex].toFixed(DECIMAL_PRECISION);
        ema50Val = ema50Data[hoveredIndex].toFixed(DECIMAL_PRECISION);
        ema200Val = ema200Data[hoveredIndex].toFixed(DECIMAL_PRECISION);
      }

      // Draw X-axis date under vertical dashed line
      const text = dateVal.toString();
      const textW = ctx.measureText(text).width;
      const textH = LABEL_FONT_SIZE;

      ctx.fillStyle = DATE_COLOR;
      ctx.fillRect(
        x - textW / 2 - BOX_PADDING / 2,
        chartArea.bottom + Y_OFFSET - textH / 2 - BOX_PADDING / 2,
        textW + BOX_PADDING,
        textH + BOX_PADDING
      );

      ctx.fillStyle = FILL_COLOR;
      ctx.textAlign = "center";
      ctx.fillText(text, x, chartArea.bottom + Y_OFFSET);

      // Get y positions for close-price, 30-EMA, 50-EMA, and 200-EMA at hovered index
      const yClose = y;
      let y30 = undefined;
      let y50 = undefined;
      let y200 = undefined;

      if (emaData) {
        y30 = chart.scales.y.getPixelForValue(ema30Val);
        y50 = chart.scales.y.getPixelForValue(ema50Val);
        y200 = chart.scales.y.getPixelForValue(ema200Val);
      }

      // Each item: { y position, value, color, dataset index }
      const values = [
        {
          y: yClose,
          value: closePriceVal,
          color: CLOSE_PRICE_COLOR,
          index: 0,
        },
      ];
      if (emaData) {
        values.unshift({
          y: y30,
          value: ema30Val,
          color: EMA_30_COLOR,
          index: 1,
        });
        values.unshift({
          y: y50,
          value: ema50Val,
          color: EMA_50_COLOR,
          index: 2,
        });
        values.unshift({
          y: y200,
          value: ema200Val,
          color: EMA_200_COLOR,
          index: 3,
        });
      }

      values.forEach(({ y, value, color, index }) => {
        if (chart.isDatasetVisible(index)) {
          const text = value.toString();
          const textW = ctx.measureText(text).width;
          const textH = LABEL_FONT_SIZE;

          ctx.textAlign = "left";

          // Fixed left position for background rectangle and text
          const leftPos = chartArea.right + X_OFFSET;

          // Draw background rectangle
          ctx.fillStyle = color;
          ctx.fillRect(
            leftPos - BOX_PADDING / 2,
            y - textH / 2 - BOX_PADDING / 2,
            textW + BOX_PADDING,
            textH + BOX_PADDING
          );

          // Draw text
          ctx.fillStyle = FILL_COLOR;
          ctx.fillText(text, leftPos, y);
        }
      });
    }

    ctx.restore();
  },
};

const htmlLegendPlugin = {
  id: "htmlLegend",
  afterUpdate(chart, args, options) {
    const ul = document.getElementById(options.containerID);

    // Clear previous legend
    ul.innerHTML = "";

    const items = chart.options.plugins.legend.labels.generateLabels(chart);

    // Only include EMA datasets
    const allowedLabels = [EMA_30_LABEL, EMA_50_LABEL, EMA_200_LABEL];
    const filteredItems = items.filter((item) =>
      allowedLabels.includes(item.text)
    );

    filteredItems.forEach((item) => {
      const li = document.createElement("li");
      li.classList.add(
        "d-flex",
        "align-items-center",
        "gap-2",
        "cursor-pointer"
      );

      // Click to toggle dataset visibility
      li.onclick = () => {
        const { type } = chart.config;
        if (type === "pie" || type === "doughnut") {
          // Pie and doughnut charts only have a single dataset and visibility is per item
          chart.toggleDataVisibility(item.index);
        } else {
          chart.setDatasetVisibility(
            item.datasetIndex,
            !chart.isDatasetVisible(item.datasetIndex)
          );
        }
        chart.update();
      };

      const colorBox = document.createElement("span");
      colorBox.classList.add(
        "d-inline-block",
        "rounded-circle",
        "flex-shrink-0"
      );
      colorBox.style.backgroundColor = item.strokeStyle;
      colorBox.style.width = `${LEGEND_CIRCLE_SIZE}px`;
      colorBox.style.height = `${LEGEND_CIRCLE_SIZE}px`;

      const label = document.createElement("span");
      label.textContent = item.text;
      label.style.textDecoration = item.hidden ? "line-through" : "";

      li.appendChild(colorBox);
      li.appendChild(label);
      ul.appendChild(li);
    });
  },
};

function handleTouch(event) {
  const touch = event.touches[0];
  const rect = stockChart.canvas.getBoundingClientRect();
  const x = touch.clientX - rect.left;
  const y = touch.clientY - rect.top;

  const point = stockChart.getElementsAtEventForMode(
    { clientX: touch.clientX, clientY: touch.clientY },
    CHART_INTERACTION_MODE,
    { intersect: CHART_INTERACTION_INTERSECT },
    false
  );

  stockChart.setActiveElements(point);
  stockChart.tooltip.setActiveElements(point, { x, y });
  stockChart.update();
}

let chartSpinnerTimeout;
function showChartSpinner() {
  const spinner = document.getElementById("chart-loading-spinner");
  if (spinner) spinner.classList.remove("d-none");
}
function hideChartSpinner() {
  const spinner = document.getElementById("chart-loading-spinner");
  if (spinner) spinner.classList.add("d-none");
  clearTimeout(chartSpinnerTimeout);
}

function activateTfBtn(button, timeframe) {
  // Deactivate all timeframe buttons
  const timeframeBtns = document.querySelectorAll(".tf-btn");
  timeframeBtns.forEach((tfButton) => {
    tfButton.removeAttribute("aria-label");
    tfButton.removeAttribute("aria-current");
    tfButton.classList.remove("active");
  });

  // Active the given timeframe button
  button.setAttribute("aria-label", `${timeframe}`);
  button.setAttribute("aria-current", "true");
  button.classList.add("active");
}

function updateTfChangePerc(changePerc) {
  if (changePerc >= 0) color = POSITIVE_COLOR;
  else color = NEGATIVE_COLOR;

  changePerc = changePerc.toFixed(DECIMAL_PRECISION);
  const formatted = `${changePerc >= 0 ? "+" : ""}${changePerc}%`;

  tfChangePerc.textContent = formatted;
  tfChangePerc.style.backgroundColor = color;
}

function createStockChart() {
  // Chart configuration
  let newStockChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: dateData,
      datasets: [
        {
          label: CLOSE_PRICE_LABEL,
          data: closePriceData,
          borderColor: CLOSE_PRICE_COLOR,
          backgroundColor: CHART_BACKGROUND_COLOR,
          tension: CHART_TENSION,
          fill: CHART_FILL,
          pointHoverRadius: POINT_HOVER_RADIUS,
          pointHoverBackgroundColor: POINT_HOVER_COLOR,
        },
        {
          label: EMA_30_LABEL,
          data: ema30Data,
          borderColor: EMA_30_COLOR,
          backgroundColor: CHART_BACKGROUND_COLOR,
          tension: CHART_TENSION,
          fill: CHART_FILL,
          borderWidth: EMA_BORDER_WIDTH,
          pointRadius: EMA_POINT_RADIUS,
        },
        {
          label: EMA_50_LABEL,
          data: ema50Data,
          borderColor: EMA_50_COLOR,
          backgroundColor: CHART_BACKGROUND_COLOR,
          tension: CHART_TENSION,
          fill: CHART_FILL,
          borderWidth: EMA_BORDER_WIDTH,
          pointRadius: EMA_POINT_RADIUS,
        },
        {
          label: EMA_200_LABEL,
          data: ema200Data,
          borderColor: EMA_200_COLOR,
          backgroundColor: CHART_BACKGROUND_COLOR,
          tension: CHART_TENSION,
          fill: CHART_FILL,
          borderWidth: EMA_BORDER_WIDTH,
          pointRadius: EMA_POINT_RADIUS,
        },
        {
          type: "bar",
          label: VOLUME_LABEL,
          data: volumeData,
          yAxisID: "volumeAxis", // To get separate Y-axis for volume bar chart
          backgroundColor: VOLUME_COLOR,
          borderSkipped: false,
          barPercentage: 1.0,
          categoryPercentage: 1.0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        // Activate the nearest data point on mouse hover
        mode: CHART_INTERACTION_MODE,
        intersect: CHART_INTERACTION_INTERSECT,
      },
      plugins: {
        tooltip: {
          enabled: displayTooltip,
          callbacks: {
            label: function (context) {
              let label = context.dataset.label || "";
              let value = context.parsed.y;
              if (label && value !== null) {
                if (label === VOLUME_LABEL)
                  label += ": " + value.toLocaleString("en-US");
                else
                  label +=
                    ": " +
                    value.toFixed(DECIMAL_PRECISION).toLocaleString("en-US");
              }
              return label;
            },
          },
        },
        legend: {
          display: false,
        },
        htmlLegend: {
          containerID: "chart-legend",
        },
        zoom: {
          pan: {
            enabled: true,
            mode: "x",
            modifierKey: null,
          },
          zoom: {
            wheel: { enabled: true },
            pinch: { enabled: true },
            mode: "x",
          },
          limits: {
            x: { minRange: ZOOM_MIN_RANGE },
          },
        },
      },
      scales: {
        x: {
          offset: false, // To make grid lines go through line chart points rather than bar chart bar widths
          grid: {
            offset: false, // To remove excess space on the right caused by bar chart
          },
          ticks: {
            maxTicksLimit: MAX_X_TICKS,
            font: {
              size: LABEL_FONT_SIZE,
            },
          },
        },
        y: {
          position: "right",
          ticks: {
            precision: DECIMAL_PRECISION,
            font: {
              size: LABEL_FONT_SIZE,
            },
            callback: function (value) {
              return value.toFixed(DECIMAL_PRECISION);
            },
          },
        },
        volumeAxis: {
          type: "linear",
          display: false, // No y-axis labels
          min: 0,
          max: Math.max(...volumeData) * VOLUME_AXIS_MAX_MULTIPLIER, // For better bar chart scaling
          grid: {
            drawOnChartArea: false, // No grid lines for volume
          },
        },
      },
    },
    plugins: [hoverPlugin, htmlLegendPlugin],
  });

  const canvas = newStockChart.canvas;
  // To be able to drag-scroll the page while on the chart on mobile
  canvas.style.touchAction = "pan-y";

  // To get same functionality on chart as mouse hover while dragging on phone
  canvas.addEventListener("touchstart", handleTouch, { passive: true });
  canvas.addEventListener("touchmove", handleTouch, { passive: true });

  newStockChart.options.scales.volumeAxis.max =
    Math.max(...volumeData) * VOLUME_AXIS_MAX_MULTIPLIER;

  return newStockChart;
}

function resetChart(button, preloadedData = null) {
  const timeframe = button.dataset.timeframe;

  const handleChartData = (data) => {
    dateData.length = 0;
    closePriceData.length = 0;
    ema30Data.length = 0;
    ema50Data.length = 0;
    ema200Data.length = 0;
    volumeData.length = 0;

    emaData = data.ema_data;
    dateData.push(...data.date_data);
    closePriceData.push(...data.close_price_data);
    volumeData.push(...data.volume_data);
    if (emaData) {
      ema30Data.push(...data.ema_30_data);
      ema50Data.push(...data.ema_50_data);
      ema200Data.push(...data.ema_200_data);
    }

    // Destroy the old chart if it exists
    if (stockChart) {
      stockChart.destroy();
    }

    const stockChartCanvas = document.getElementById("stock-chart");
    const missingDataOverlay = document.getElementById(
      "stock-chart-missing-data"
    );
    if (dateData.length != 0 && closePriceData.length != 0) {
      // Show chart, hide "missing data" text
      stockChartCanvas.classList.remove("d-none");
      missingDataOverlay.classList.add("d-none");

      stockChart = createStockChart();

      // Update the hover info text with the most recent values
      // from the datasets as the initial values
      updateHoverInfoText(-1);
    } else {
      // Hide chart, show "missing data" text
      stockChartCanvas.classList.add("d-none");
      missingDataOverlay.classList.remove("d-none");

      updateHoverInfoText(null);
    }

    activateTfBtn(button, timeframe);
    updateTfChangePerc(data.change_perc);
  };

  if (preloadedData) {
    handleChartData(preloadedData);
  } else {
    chartSpinnerTimeout = setTimeout(showChartSpinner, CHART_SPINNER_DELAY);
    fetch(
      `/chart-data?ticker=${encodeURIComponent(ticker)}&timeframe=${timeframe}`
    )
      .then((response) => response.json())
      .then((data) => {
        hideChartSpinner();
        handleChartData(data);
      })
      .catch((error) => {
        hideChartSpinner();
      });
  }
}

const ticker = document.getElementById("stock-chart").dataset.ticker;
resetChart(
  document.querySelector(`.tf-btn[data-timeframe="${initialTimeframe}"]`),
  initialStockChartData
);

const timeframeBtns = document.querySelectorAll(".tf-btn");
timeframeBtns.forEach((button) => {
  button.addEventListener("click", (event) => {
    resetChart(event.currentTarget);
  });
});
