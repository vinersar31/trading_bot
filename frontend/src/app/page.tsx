import PlotlyChart from "@/components/PlotlyChart";
import { promises as fs } from 'fs';
import path from 'path';

export default async function Home() {
    // Read stats and chart JSON files directly
    const statsPath = path.join(process.cwd(), 'public', 'stats.json');
    const chartPath = path.join(process.cwd(), 'public', 'chart.json');

    let stats: any = null;
    let chart: any = null;

    try {
        const statsData = await fs.readFile(statsPath, 'utf8');
        stats = JSON.parse(statsData);

        const chartData = await fs.readFile(chartPath, 'utf8');
        chart = JSON.parse(chartData);
    } catch (e) {
        console.error("Error reading data:", e);
    }

    if (!stats || !chart) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-gray-900 text-white">
                <p>Data not found. Please run the simulation first.</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-900 text-white p-6 font-sans">
            <div className="max-w-7xl mx-auto space-y-8">

                {/* Header */}
                <div className="text-center">
                    <h1 className="text-4xl font-bold tracking-tight">Multi-Asset Trading Bot Dashboard</h1>
                    <p className="mt-2 text-gray-400">Simulation performance and backtest results</p>
                </div>

                {/* Scorecards */}
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                    <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
                        <p className="text-sm text-gray-400 uppercase tracking-wider">Initial Capital</p>
                        <p className="text-2xl font-semibold mt-1">${stats.initialValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
                    </div>

                    <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
                        <p className="text-sm text-gray-400 uppercase tracking-wider">Final Value</p>
                        <p className="text-2xl font-semibold mt-1">${stats.finalValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
                    </div>

                    <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
                        <p className="text-sm text-gray-400 uppercase tracking-wider">Total Return</p>
                        <p className={`text-2xl font-semibold mt-1 ${stats.totalReturn >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {stats.totalReturn >= 0 ? '+' : ''}{stats.totalReturn.toFixed(2)}%
                        </p>
                    </div>

                    <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
                        <p className="text-sm text-gray-400 uppercase tracking-wider">Max Drawdown</p>
                        <p className="text-2xl font-semibold mt-1 text-red-400">
                            {stats.maxDrawdown.toFixed(2)}%
                        </p>
                    </div>

                    <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
                        <p className="text-sm text-gray-400 uppercase tracking-wider">Total Trades</p>
                        <p className="text-2xl font-semibold mt-1">{stats.numTrades}</p>
                    </div>

                    <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
                        <p className="text-sm text-gray-400 uppercase tracking-wider">Win Rate</p>
                        <p className="text-2xl font-semibold mt-1">
                            {stats.winRate.toFixed(1)}% <span className="text-sm text-gray-400">({stats.winTrades}/{stats.totalCompletedTrades})</span>
                        </p>
                    </div>
                </div>

                {/* Chart Section */}
                <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden shadow-xl" style={{ height: '800px' }}>
                    {/* We clear out the title from layout since we rendered it above */}
                    <PlotlyChart
                        data={chart.data}
                        layout={{
                            ...chart.layout,
                            title: '',
                            margin: { t: 60, r: 20, l: 40, b: 40 },
                            paper_bgcolor: 'rgba(0,0,0,0)',
                            plot_bgcolor: 'rgba(0,0,0,0)',
                            height: 800
                        }}
                    />
                </div>

            </div>
        </div>
    );
}
