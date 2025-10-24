// Target is hardcoded for Ecoaims 10m air pistol system in this version.
function create_series_plot(series) {
  const svg = d3.select("#mySVG");
  const width = +svg.attr("width");
  const height = +svg.attr("height");
  const tooltip = d3.select("#tooltip");

  // Define vertical gradient
  svg.append("defs")
    .append("linearGradient")
    .attr("id", "grayGradient")
    .attr("x1", "0%")
    .attr("y1", "0%")
    .attr("x2", "0%")
    .attr("y2", "100%")
    .selectAll("stop")
    .data([
      { offset: "0%", color: "#dddddd" },
      { offset: "100%", color: "#888888" }
    ])
    .enter()
    .append("stop")
    .attr("offset", d => d.offset)
    .attr("stop-color", d => d.color);

  svg.append("rect")
    .attr("x", 0)
    .attr("y", 0)
    .attr("width", width)
    .attr("height", height)
    .attr("fill", "url(#grayGradient)");

  // Center and scale
  const x0 = Math.floor(width / 2);
  const y0 = Math.floor(height / 2);
  const scale = 2.2; // FIXME: should this be a parameter?

  // Draw target rings
  const ringRadii = [59.5, 5.5, 11.5, 27.5, 43.5].map(v => Math.floor(0.5 * v * scale));
  const ringColors = ["#000000", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFFFFF"];

  svg.append("circle")
    .attr("cx", x0)
    .attr("cy", y0)
    .attr("r", Math.floor(0.5 * 155.5 * scale))
    .attr("fill", "#FFFFFF")
    .attr("stroke", "#FFFFFF");

  ringRadii.forEach((r, i) => {
    svg.append("circle")
      .attr("cx", x0)
      .attr("cy", y0)
      .attr("r", r)
      .attr("fill", i === 0 ? "#000000" : "none")
      .attr("stroke", ringColors[i]);
  });

  const xList = [75.5, 91.5, 107.5, 123.5, 139.5, 155.5];
  xList.forEach(r => {
    svg.append("circle")
      .attr("cx", x0)
      .attr("cy", y0)
      .attr("r", Math.floor(0.5 * r * scale))
      .attr("fill", "none")
      .attr("stroke", "#000000");
  });

  // Shot markers and points for each shot
  const shotTuples = series.shots.map(shot => [shot.x, shot.y]);
  const shotPoints = series.shots.map(shot => shot.points);

  // Create a group for each shot
  const shotGroup = svg.selectAll("g.shot")
    .data(shotTuples)
    .enter()
    .append("g")
    .attr("class", "shot")
    .attr("transform", d => `translate(${d})`);

  // Draw shot circle
  shotGroup.append("circle")
    .attr("r", Math.floor(5 * scale))
    .attr("fill", "#fbff00ff")
    .attr("stroke", "#000000");

  // Add annotation inside the circle
  shotGroup.append("text")
    .attr("text-anchor", "middle")
    .attr("dominant-baseline", "middle")
    .attr("fill", "#000000")
    .attr("font-size", "10px")
    .text((_, i) => i + 1);

  // Tooltip behavior
  shotGroup
    .on("mouseover", function (event, d) {
      const index = shotGroup.nodes().indexOf(this);
      const label = index >= 0 ? shotPoints[index] : '?';
      tooltip
        .style("visibility", "visible")
        .text(`${label}`);
    })
    .on("mousemove", function (event) {
      tooltip
        .style("top", (event.pageY + 10) + "px")
        .style("left", (event.pageX + 10) + "px");
    })
    .on("mouseout", function () {
      tooltip.style("visibility", "hidden");
    });
  }
