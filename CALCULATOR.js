// 🎯 COMPLETE DUCT CALCULATOR AUTOMATION SCRIPT
// Copy this entire script and run it on the calculator page

class DuctCalculatorAutomator {
    constructor() {
        this.baseUrl = 'https://ssccust1.spreadsheethosting.com/1/0c/12832d7e46eda9/cduct-rectSI170927/cduct-rectSI170927.htm';
        this.results = [];
    }

    // 🔧 Set a field value and trigger updates
    setField(fieldId, value) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = value;
            field.dispatchEvent(new Event('input', { bubbles: true }));
            field.dispatchEvent(new Event('change', { bubbles: true }));
            field.dispatchEvent(new Event('blur', { bubbles: true }));
            console.log(`✅ Set ${fieldId} to: ${value}`);
            return true;
        } else {
            console.log(`❌ Field ${fieldId} not found`);
            return false;
        }
    }

    // 🔽 Set dropdown value
    setDropdown(fieldId, value) {
        const dropdown = document.getElementById(fieldId);
        if (dropdown) {
            dropdown.value = value;
            dropdown.dispatchEvent(new Event('change', { bubbles: true }));
            console.log(`✅ Set dropdown ${fieldId} to: ${value}`);
            return true;
        } else {
            console.log(`❌ Dropdown ${fieldId} not found`);
            return false;
        }
    }

    // 📊 Get all calculated results
    getResults() {
        const resultFields = {
            equivalentDiameter: 'XLEW_3_6_2',
            averageVelocity: 'XLEW_3_8_2',
            effectiveVelocity: 'XLEW_3_9_2',
            pressureDrop: 'XLEW_3_10_2',
            velocityPressure: 'XLEW_3_12_2',
            crossSectionalArea: 'XLEW_3_15_2',
            absoluteRoughness: 'XLEW_3_16_2',
            relativeRoughness: 'XLEW_3_17_2',
            density: 'XLEW_3_23_2',
            dynamicViscosity: 'XLEW_3_24_2',
            massFlow: 'XLEW_3_25_2',
            reynoldsNumber: 'XLEW_3_26_2',
            flowType: 'XLEW_3_27_1'
        };

        const results = {};
        for (const [key, fieldId] of Object.entries(resultFields)) {
            const field = document.getElementById(fieldId);
            if (field) {
                results[key] = field.value;
            }
        }
        return results;
    }

    // 🎯 Calculate single scenario
    async calculateScenario(params) {
        console.log(`🔥 Calculating scenario: ${JSON.stringify(params)}`);
        
        // Set input parameters
        if (params.flowrate) this.setField('XLEW_3_4_2', params.flowrate);
        if (params.width) this.setField('XLEW_3_5_2', params.width);
        if (params.height) this.setField('XLEW_3_5_3', params.height);
        if (params.temperature) this.setField('XLEW_3_19_2', params.temperature);
        if (params.humidity) this.setField('XLEW_3_21_2', params.humidity);
        if (params.material) this.setDropdown('XLEW_3_3_1', params.material);
        if (params.flowUnits) this.setDropdown('XLEW_3_4_3', params.flowUnits);

        // Wait for calculation to complete
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Get results
        const results = this.getResults();
        const scenario = {
            input: params,
            output: results,
            timestamp: new Date().toISOString()
        };

        this.results.push(scenario);
        console.log('📊 Results:', results);
        return scenario;
    }

    // 🚀 Run multiple scenarios
    async runBatchCalculations(scenarios) {
        console.log(`🎯 Running ${scenarios.length} scenarios...`);
        
        for (let i = 0; i < scenarios.length; i++) {
            console.log(`\n--- Scenario ${i + 1}/${scenarios.length} ---`);
            await this.calculateScenario(scenarios[i]);
            
            // Small delay between calculations
            await new Promise(resolve => setTimeout(resolve, 500));
        }

        console.log('\n🎉 All calculations complete!');
        return this.results;
    }

    // 📋 Export results to CSV
    exportToCSV() {
        if (this.results.length === 0) {
            console.log('❌ No results to export');
            return;
        }

        const headers = [
            'Flowrate', 'Width', 'Height', 'Temperature', 'Humidity', 'Material',
            'Equivalent Diameter', 'Average Velocity', 'Pressure Drop', 'Reynolds Number'
        ];

        let csv = headers.join(',') + '\n';

        this.results.forEach(result => {
            const row = [
                result.input.flowrate || '',
                result.input.width || '',
                result.input.height || '',
                result.input.temperature || '',
                result.input.humidity || '',
                result.input.material || '',
                result.output.equivalentDiameter || '',
                result.output.averageVelocity || '',
                result.output.pressureDrop || '',
                result.output.reynoldsNumber || ''
            ];
            csv += row.join(',') + '\n';
        });

        // Download CSV
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `duct_calculations_${new Date().toISOString().slice(0,10)}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);

        console.log('📁 CSV exported successfully!');
    }

    // 📊 Display results table
    displayResults() {
        if (this.results.length === 0) {
            console.log('❌ No results to display');
            return;
        }

        console.log('\n📊 === CALCULATION RESULTS ===');
        console.table(this.results.map(r => ({
            Flowrate: r.input.flowrate,
            Dimensions: `${r.input.width}x${r.input.height}`,
            'Equiv Diameter': r.output.equivalentDiameter,
            'Avg Velocity': r.output.averageVelocity,
            'Pressure Drop': r.output.pressureDrop,
            'Reynolds No': r.output.reynoldsNumber
        })));
    }
}

// 🎯 READY TO USE!
console.log('🎯 Duct Calculator Automator loaded!');
console.log('📋 Usage examples:');
console.log('');
console.log('// Create automator instance');
console.log('const calc = new DuctCalculatorAutomator();');
console.log('');
console.log('// Single calculation');
console.log('await calc.calculateScenario({');
console.log('    flowrate: 200,');
console.log('    width: 300,');
console.log('    height: 250,');
console.log('    temperature: 25,');
console.log('    material: "Galvanised steel"');
console.log('});');
console.log('');
console.log('// Batch calculations');
console.log('const scenarios = [');
console.log('    {flowrate: 100, width: 200, height: 200},');
console.log('    {flowrate: 150, width: 250, height: 200},');
console.log('    {flowrate: 200, width: 300, height: 250}');
console.log('];');
console.log('await calc.runBatchCalculations(scenarios);');
console.log('');
console.log('// Export results');
console.log('calc.exportToCSV();');
console.log('calc.displayResults();');
