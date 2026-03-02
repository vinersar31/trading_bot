"use client";

import dynamic from "next/dynamic";
import React from "react";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export default function PlotlyChart({ data, layout }: { data: any, layout: any }) {
    return (
        <Plot
            data={data}
            layout={{...layout, autosize: true}}
            useResizeHandler={true}
            style={{ width: "100%", height: "100%", minHeight: "800px" }}
            config={{ responsive: true }}
        />
    );
}
