// Colors
const DATE_COLOR = "rgba(100, 100, 100, 1)";
const CLOSE_PRICE_COLOR = "rgba(54, 220, 235, 1)";
const EMA_30_COLOR = "rgba(0, 251, 25, 1)";
const EMA_50_COLOR = "rgba(251, 188, 0, 1)";
const EMA_200_COLOR = "rgba(255, 0, 0, 1)";
const VOLUME_COLOR = "rgba(78, 140, 255, 0.75)";
const FILL_COLOR = "rgba(255, 255, 255, 1)";
const STROKE_STYLE = "rgba(0,0,0,0.4)";
const POINT_HOVER_COLOR = "rgba(100, 0, 255, 1)";
const TF_TOOLTIP_TEXT_COLOR = "white";

// Limits
const MAX_X_TICKS = 12;
const ZOOM_MIN_RANGE = 5; // minimum number of values to show when zoomed in
const DECIMAL_PRECISION = 2;
const DISPLAY_TOOLTIP_DEFAULT = false; // OFF by default

// Sizing
const VOLUME_AXIS_MAX_MULTIPLIER = 5; // volume bars take (1/multplier) height of the chart
const POINT_HOVER_RADIUS = 7;
const EMA_BORDER_WIDTH = 1.5;
const EMA_POINT_RADIUS = 0;
const X_OFFSET = 28;
const Y_OFFSET = 18;
const BOX_PADDING = 4;
const LINE_DASH = [5, 5];
const LINE_WIDTH = 1;

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

let displayTooltip = DISPLAY_TOOLTIP_DEFAULT;

const dateValue = document.getElementById("date-value");
const closePriceValue = document.getElementById("close-price-value");
const ema30Value = document.getElementById("ema-30-value");
const ema50Value = document.getElementById("ema-50-value");
const ema200Value = document.getElementById("ema-200-value");
const volumeValue = document.getElementById("volume-value");

function updateHoverInfoText(
  dateVal,
  closePriceVal,
  ema30Val,
  ema50Val,
  ema200Val,
  volumeVal
) {
  dateValue.textContent = `${DATE_LABEL}: ${dateVal}`;
  closePriceValue.textContent = `${CLOSE_PRICE_LABEL}: ${closePriceVal.toFixed(
    DECIMAL_PRECISION
  )}`;
  ema30Value.textContent = `${EMA_30_LABEL}: ${ema30Val.toFixed(
    DECIMAL_PRECISION
  )}`;
  ema50Value.textContent = `${EMA_50_LABEL}: ${ema50Val.toFixed(
    DECIMAL_PRECISION
  )}`;
  ema200Value.textContent = `${EMA_200_LABEL}: ${ema200Val.toFixed(
    DECIMAL_PRECISION
  )}`;
  volumeValue.textContent = `${VOLUME_LABEL}: ${volumeVal}`;
}

updateHoverInfoText(
  dateData.at(-1),
  closePriceData.at(-1),
  ema30Data.at(-1),
  ema50Data.at(-1),
  ema200Data.at(-1),
  volumeData.at(-1)
);

dateValue.style.color = DATE_COLOR;
closePriceValue.style.color = CLOSE_PRICE_COLOR;
ema30Value.style.color = EMA_30_COLOR;
ema50Value.style.color = EMA_50_COLOR;
ema200Value.style.color = EMA_200_COLOR;
volumeValue.style.color = VOLUME_COLOR;

const tooltipToggle = document.getElementById("tooltip-toggle");
tooltipToggle.checked = displayTooltip;

const ctx = document.getElementById("stock-chart").getContext("2d");

// Hover Plugin:
// Draw Hover vertical/horizontal dashed lines +
// Update Hover info on top left +
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
      const dateVal = dateData[hoveredIndex];
      const closePriceVal = closePriceData[hoveredIndex];
      const ema30val = ema30Data[hoveredIndex];
      const ema50val = ema50Data[hoveredIndex];
      const ema200Val = ema200Data[hoveredIndex];
      const volumeVal = volumeData[hoveredIndex];
      updateHoverInfoText(
        dateVal,
        closePriceVal,
        ema30val,
        ema50val,
        ema200Val,
        volumeVal
      );

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
      const y200 = chart.scales.y.getPixelForValue(ema200Val);
      const y50 = chart.scales.y.getPixelForValue(ema50val);
      const y30 = chart.scales.y.getPixelForValue(ema30val);
      const yClose = y;

      // Each item: { y position, value, color, dataset index }
      const values = [
        {
          y: y200,
          value: ema200Val.toFixed(DECIMAL_PRECISION),
          color: EMA_200_COLOR,
          index: 2,
        },
        {
          y: y50,
          value: ema50val.toFixed(DECIMAL_PRECISION),
          color: EMA_50_COLOR,
          index: 1,
        },
        {
          y: y30,
          value: ema30val.toFixed(DECIMAL_PRECISION),
          color: EMA_30_COLOR,
          index: 1,
        },
        {
          y: yClose,
          value: closePriceVal.toFixed(DECIMAL_PRECISION),
          color: CLOSE_PRICE_COLOR,
          index: 0,
        },
      ];

      values.forEach(({ y, value, color, index }) => {
        if (chart.isDatasetVisible(index)) {
          const text = value.toString();
          const textW = ctx.measureText(text).width;
          const textH = LABEL_FONT_SIZE;

          ctx.fillStyle = color;
          ctx.fillRect(
            chartArea.right + X_OFFSET - textW / 2 - BOX_PADDING / 2,
            y - textH / 2 - BOX_PADDING / 2,
            textW + BOX_PADDING,
            textH + BOX_PADDING
          );

          ctx.fillStyle = FILL_COLOR;
          ctx.textAlign = "center";
          ctx.fillText(text, chartArea.right + X_OFFSET, y);
        }
      });
    }

    ctx.restore();
  },
};

// Chart configuration
const stockChart = new Chart(ctx, {
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
      },
      legend: {
        position: "top",
        align: "end",
        labels: {
          filter: (legendItem) =>
            legendItem.text === EMA_30_LABEL ||
            legendItem.text === EMA_50_LABEL ||
            legendItem.text === EMA_200_LABEL,
        },
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
  plugins: [hoverPlugin],
});

const canvas = stockChart.canvas;
// To be able to drag-scroll the page while on the chart on mobile
canvas.style.touchAction = "pan-y";

// To get same functionality on chart as mouse hover while dragging on phone
canvas.addEventListener("touchstart", handleTouch);
canvas.addEventListener("touchmove", handleTouch);

function handleTouch(event) {
  const touch = event.touches[0];
  const rect = canvas.getBoundingClientRect();
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

// Handle tooltop toggle event
tooltipToggle.addEventListener("change", function () {
  displayTooltip = tooltipToggle.checked;

  // Dynamically enable/disable tooltip display while keeping its internal state alive
  stockChart.options.plugins.tooltip.enabled = displayTooltip;
  stockChart.update();
});

// To show the active timeframe(tf) tooltip
const activeTfBtn = document.querySelector(".tf-btn.active");
// Create a tf tooltip manually
const tfTooltip = new bootstrap.Tooltip(activeTfBtn, {
  trigger: "manual",
});
tfTooltip.show();

// Get the hex color from CSS variable set via inline style
const tfTooltipColor = getComputedStyle(activeTfBtn)
  .getPropertyValue("--tooltip-bg-color")
  .trim();
// After showing, apply color manually
const tfTooltipEl = document.querySelector(".tooltip.show .tooltip-inner");
if (tfTooltipEl && tfTooltipColor) {
  tfTooltipEl.style.backgroundColor = tfTooltipColor;
  tfTooltipEl.style.color = TF_TOOLTIP_TEXT_COLOR;
  tfTooltipEl.classList.add("fw-semibold");
}
