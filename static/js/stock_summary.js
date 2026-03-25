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
  const validData = data.filter(
    (v) => v !== null && v !== undefined && !isNaN(v),
  );

  // Fallback if no valid data
  if (!validData.length) {
    validData.push(0);
  }

  let minPrice = Math.min(...validData);
  let maxPrice = Math.max(...validData);

  // Flat data (e.g., all 0s)
  if (minPrice === maxPrice) {
    if (minPrice === 0) {
      minPrice = -1;
      maxPrice = 1;
    } else {
      const offset = Math.abs(minPrice) * 0.1 || 1;
      minPrice -= offset;
      maxPrice += offset;
    }
  }

  let buffer = (maxPrice - minPrice) * BUFFER_PERC;

  // Apply transparency
  backgroundColor = backgroundColor.map((color) =>
    changeTransparency(color, BAR_TRANSPARENCY),
  );

  // Get the current theme
  const theme = CHART_THEMES[getCurrentTheme()];

  const newSummaryChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          data: data.map((v) =>
            v === null || v === undefined || isNaN(v) ? 0 : v,
          ),
          backgroundColor: backgroundColor,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: {
            color: theme.grid,
          },
          ticks: {
            color: theme.axisText,
          },
        },
        y: {
          min: minPrice - buffer,
          max: maxPrice + buffer,
          grid: {
            color: theme.grid,
          },
          ticks: {
            display: false,
          },
          title: {
            display: true,
            text: Y_AXIS_TITLE,
            font: {
              weight: "bold",
            },
            color: theme.axisText,
          },
        },
      },
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          callbacks: {
            label: (ctx) =>
              `$${Number(ctx.parsed.y || 0).toFixed(DECIMAL_PRECISION)}`,
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
            return `$${Number(value || 0).toFixed(DECIMAL_PRECISION)}`;
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
const ohlcChartLabels = ["Open", "High", "Low", "Price"];
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
  ohlcChartBackgroundColors,
);

const dmaChartCtx = document.getElementById("dma-chart").getContext("2d");
const dmaChartLabels = ["Price", "30-DMA", "50-DMA", "200-DMA"];
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
  dmaChartBackgroundColors,
);

const range52wChartCtx = document
  .getElementById("range-52w-chart")
  .getContext("2d");
const range52wChartLabels = ["52w Low", "Price", "52w High"];
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
  range52wChartBackgroundColors,
);

window.addEventListener("themechange", () => {
  if (ohlcChart) {
    updateSummaryChart(ohlcChart);
  }

  if (dmaChart) {
    updateSummaryChart(dmaChart);
  }

  if (range52wChart) {
    updateSummaryChart(range52wChart);
  }

  function updateSummaryChart(chart) {
    const theme = CHART_THEMES[getCurrentTheme()];

    chart.options.scales.x.grid.color = theme.grid;
    chart.options.scales.y.grid.color = theme.grid;

    chart.options.scales.x.ticks.color = theme.axisText;
    chart.options.scales.y.title.color = theme.axisText;

    chart.update();
  }
});
