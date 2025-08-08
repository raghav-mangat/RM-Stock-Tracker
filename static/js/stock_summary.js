const BUFFER_PERC = 0.2;
const BAR_TRANSPARENCY = 0.75;
const Y_AXIS_TITLE = "Price ($)";
const DATA_LABEL_COLOR = "#fff";
const DATA_LABEL_BACKGROUND = "#343a40";
const DATA_LABEL_BORDER_RADIUS = 4;
const DATA_LABEL_PADDING = 4;

// Function to change the alpha value
function changeTransparency(rgbaString, newAlpha) {
  // Extract the R, G, B values and the current alpha
  const parts = rgbaString.match(/rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)/);

  if (!parts) {
    return rgbaString; // Return original if format is incorrect
  }

  const r = parts[1];
  const g = parts[2];
  const b = parts[3];

  // Ensure newAlpha is within valid range (0 to 1)
  const clampedAlpha = Math.max(0, Math.min(1, newAlpha));

  // Construct the new RGBA string
  return `rgba(${r}, ${g}, ${b}, ${clampedAlpha})`;
}

function createSummaryChart(ctx, labels, data, backgroundColor) {
  const minPrice = Math.min(...data);
  const maxPrice = Math.max(...data);
  const buffer = (maxPrice - minPrice) * BUFFER_PERC; // Add buffer for better visual separation
  backgroundColor.forEach((value, index, array) => {
    array[index] = changeTransparency(value, BAR_TRANSPARENCY);
  });

  const newSummaryChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          data: data,
          backgroundColor: backgroundColor,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: minPrice - buffer,
          max: maxPrice + buffer,
          ticks: {
            display: false,
          },
          title: {
            display: true,
            text: Y_AXIS_TITLE,
            font: {
              weight: "bold",
            },
          },
        },
      },
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          callbacks: {
            label: (ctx) => `$${ctx.parsed.y.toFixed(DECIMAL_PRECISION)}`,
          },
        },
        datalabels: {
          anchor: "end",
          align: "center",
          color: DATA_LABEL_COLOR,
          backgroundColor: DATA_LABEL_BACKGROUND,
          borderRadius: DATA_LABEL_BORDER_RADIUS,
          padding: DATA_LABEL_PADDING,
          formatter: function (value) {
            return `$${value.toFixed(DECIMAL_PRECISION)}`;
          },
          font: {
            weight: "bold",
          },
        },
      },
    },
    plugins: [ChartDataLabels],
  });

  return newSummaryChart;
}

const ohlcChartCtx = document.getElementById("ohlc-chart").getContext("2d");
const ohlcChartLabels = ["Open", "High", "Low", "Close"];
const ohlcChartData = [
  stockData.day_open,
  stockData.day_high,
  stockData.day_low,
  stockData.day_close,
];
const ohlcChartBackgroundColors = [
  CLOSE_PRICE_COLOR,
  POSITIVE_COLOR,
  NEGATIVE_COLOR,
  CLOSE_PRICE_COLOR,
];
const ohlcChart = createSummaryChart(
  ohlcChartCtx,
  ohlcChartLabels,
  ohlcChartData,
  ohlcChartBackgroundColors
);

const dmaChartCtx = document.getElementById("dma-chart").getContext("2d");
const dmaChartLabels = ["Day Close", "30-DMA", "50-DMA", "200-DMA"];
const dmaChartData = [
  stockData.day_close,
  stockData.dma_30,
  stockData.dma_50,
  stockData.dma_200,
];
const dmaChartBackgroundColors = [
  CLOSE_PRICE_COLOR,
  EMA_30_COLOR,
  EMA_50_COLOR,
  EMA_200_COLOR,
];
const dmaChart = createSummaryChart(
  dmaChartCtx,
  dmaChartLabels,
  dmaChartData,
  dmaChartBackgroundColors
);

const range52wChartCtx = document
  .getElementById("range-52w-chart")
  .getContext("2d");
const range52wChartLabels = ["52w Low", "Day Close", "52w High"];
const range52wChartData = [
  stockData.low_52w,
  stockData.day_close,
  stockData.high_52w,
];
const range52wChartBackgroundColors = [
  NEGATIVE_COLOR,
  CLOSE_PRICE_COLOR,
  POSITIVE_COLOR,
];
const range52wChart = createSummaryChart(
  range52wChartCtx,
  range52wChartLabels,
  range52wChartData,
  range52wChartBackgroundColors
);
