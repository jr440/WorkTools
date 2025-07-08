/**
 * HVAC Duct Calculator Automator
 * Advanced duct sizing and analysis tool
 */

class DuctCalculatorAutomator {
    constructor() {
        console.log('Duct Calculator Automator initialized');
        
        // Material roughness values in mm
        this.materialRoughness = {
            'Galvanized Steel': 0.0015,
            'Aluminum': 0.0015,
            'Stainless Steel': 0.0015,
            'PVC': 0.0015,
            'Fiberglass': 0.003
        };
    }
    
    /**
     * Perform duct calculations based on input parameters
     * @param {Object} params - Input parameters
     * @returns {Object} Calculation results
     */
    performCalculation(params) {
        // Convert flow rate to m³/s if needed
        let flowRate = params.flowrate;
        switch(params.flowUnits) {
            case 'L/s':
                flowRate = flowRate / 1000;
                break;
            case 'CFM':
                flowRate = flowRate * 0.000471947;
                break;
            // m³/s is already correct
        }

        // Convert dimensions to meters
        const width = params.width / 1000;
        const height = params.height / 1000;
        
        // Calculate cross-sectional area
        const area = width * height;
        
        // Calculate hydraulic diameter (equivalent diameter)
        const hydraulicDiameter = (4 * area / (2 * (width + height)));
        const equivalentDiameter = hydraulicDiameter * 1000; // Convert to mm
        
        // Calculate velocity
        const velocity = flowRate / area;
        
        // Calculate air properties
        const airProperties = this.calculateAirProperties(params.temperature, params.humidity);
        const airDensity = airProperties.density;
        const kinematicViscosity = airProperties.kinematicViscosity;
        
        // Calculate velocity pressure
        const velocityPressure = 0.5 * airDensity * Math.pow(velocity, 2);
        
        // Calculate Reynolds number
        const reynoldsNumber = velocity * hydraulicDiameter / kinematicViscosity;
        
        // Determine flow type
        const flowType = reynoldsNumber > 4000 ? 'Turbulent' : reynoldsNumber > 2300 ? 'Transitional' : 'Laminar';
        
        // Get material roughness
        const roughness = this.materialRoughness[params.material] || 0.0015; // Default to galvanized steel
        
        // Calculate friction factor
        const frictionFactor = this.calculateFrictionFactor(reynoldsNumber, roughness, equivalentDiameter);
        
        // Calculate pressure drop per meter
        const pressureDrop = frictionFactor * (airDensity * Math.pow(velocity, 2)) / (2 * hydraulicDiameter);
        
        // Calculate effective velocity (accounting for boundary layer)
        const effectiveVelocity = velocity * (1 - 0.02); // Simplified boundary layer effect

        return {
            input: params,
            output: {
                equivalentDiameter: equivalentDiameter.toFixed(1),
                averageVelocity: velocity.toFixed(2),
                effectiveVelocity: effectiveVelocity.toFixed(2),
                pressureDrop: pressureDrop.toFixed(2),
                velocityPressure: velocityPressure.toFixed(2),
                crossSectionalArea: (area * 1000000).toFixed(0), // Convert to mm²
                reynoldsNumber: Math.round(reynoldsNumber),
                flowType: flowType,
                frictionFactor: frictionFactor.toFixed(4),
                airDensity: airDensity.toFixed(3)
            }
        };
    }
    
    /**
     * Calculate air properties based on temperature and humidity
     * @param {number} temperature - Air temperature in °C
     * @param {number} humidity - Relative humidity in %
     * @returns {Object} Air properties
     */
    calculateAirProperties(temperature, humidity) {
        // Simplified air density calculation
        const density = 1.225 * (293.15 / (273.15 + temperature));
        
        // Simplified kinematic viscosity calculation
        const kinematicViscosity = 1.5e-5 * Math.pow((273.15 + temperature) / 293.15, 0.7);
        
        return {
            density: density,
            kinematicViscosity: kinematicViscosity
        };
    }
    
    /**
     * Calculate friction factor using Colebrook-White equation
     * @param {number} reynolds - Reynolds number
     * @param {number} roughness - Material roughness in mm
     * @param {number} diameter - Equivalent diameter in mm
     * @returns {number} Friction factor
     */
    calculateFrictionFactor(reynolds, roughness, diameter) {
        const relativeRoughness = roughness / diameter;
        
        if (reynolds < 2300) {
            // Laminar flow
            return 64 / reynolds;
        } else if (reynolds < 4000) {
            // Transitional flow - interpolate between laminar and turbulent
            const laminarFactor = 64 / reynolds;
            const turbulentFactor = this.calculateTurbulentFrictionFactor(reynolds, relativeRoughness);
            const x = (reynolds - 2300) / (4000 - 2300);
            return laminarFactor * (1 - x) + turbulentFactor * x;
        } else {
            // Turbulent flow
            return this.calculateTurbulentFrictionFactor(reynolds, relativeRoughness);
        }
    }
    
    /**
     * Calculate turbulent friction factor using Colebrook-White approximation
     * @param {number} reynolds - Reynolds number
     * @param {number} relativeRoughness - Relative roughness
     * @returns {number} Friction factor
     */
    calculateTurbulentFrictionFactor(reynolds, relativeRoughness) {
        // Haaland approximation of Colebrook-White equation
        return Math.pow(-1.8 * Math.log10(Math.pow(relativeRoughness/3.7, 1.11) + 6.9/reynolds), -2);
    }
    
    /**
     * Find optimal duct size with one dimension locked
     * @param {Object} params - Input parameters including locked dimension
     * @returns {Object} Optimal dimensions
     */
    findSemiOptimalSize(params) {
        // Convert flow rate to m³/s
        let flowRateM3S = params.flowrate;
        switch(params.flowUnits) {
            case 'L/s':
                flowRateM3S = params.flowrate / 1000;
                break;
            case 'CFM':
                flowRateM3S = params.flowrate * 0.000471947;
                break;
        }
        
        // Get the locked dimension in meters
        const lockedValue = params.lockedValue / 1000;
        const isWidthLocked = params.lockedDimension === 'width';
        
        // Calculate the other dimension based on maximum velocity
        let otherDimension = flowRateM3S / (params.maxVelocity * lockedValue);
        
        // Get size increment in meters
        const increment = parseInt(params.sizeIncrement || 50) / 1000;
        
        // Convert to mm and round to size increment
        otherDimension = otherDimension * 1000;
        otherDimension = Math.ceil(otherDimension / params.sizeIncrement) * params.sizeIncrement;
        
        // Prepare result object with the dimensions
        let width, height;
        if (isWidthLocked) {
            width = params.lockedValue;
            height = otherDimension;
        } else {
            width = otherDimension;
            height = params.lockedValue;
        }
        
        // Check if the calculated dimensions meet the constraints
        const testParams = {
            flowrate: params.flowrate,
            width: width,
            height: height,
            temperature: params.temperature,
            humidity: params.humidity,
            material: params.material,
            flowUnits: params.flowUnits
        };
        
        const result = this.performCalculation(testParams);
        const velocity = parseFloat(result.output.averageVelocity);
        const pressureDrop = parseFloat(result.output.pressureDrop);
        
        // If pressure drop is too high, try to adjust the other dimension
        if (pressureDrop > params.maxPressureDrop) {
            // Iteratively increase the non-locked dimension until pressure drop is acceptable
            let iterations = 0;
            const maxIterations = 20; // Prevent infinite loops
            let currentOtherDimension = otherDimension;
            
            while (pressureDrop > params.maxPressureDrop && iterations < maxIterations) {
                // Increase by one increment each time
                currentOtherDimension += parseInt(params.sizeIncrement);
                
                // Update dimensions
                if (isWidthLocked) {
                    height = currentOtherDimension;
                } else {
                    width = currentOtherDimension;
                }
                
                // Recalculate with new dimensions
                const newParams = {
                    flowrate: params.flowrate,
                    width: width,
                    height: height,
                    temperature: params.temperature,
                    humidity: params.humidity,
                    material: params.material,
                    flowUnits: params.flowUnits
                };
                
                const newResult = this.performCalculation(newParams);
                const newPressureDrop = parseFloat(newResult.output.pressureDrop);
                
                // If we've reached an acceptable pressure drop, break the loop
                if (newPressureDrop <= params.maxPressureDrop) {
                    return {
                        width: Math.round(width),
                        height: Math.round(height),
                        velocity: parseFloat(newResult.output.averageVelocity),
                        pressureDrop: newPressureDrop
                    };
                }
                
                iterations++;
            }
            
            // If we couldn't find a solution that meets constraints
            throw new Error("Constraints not met - adjust parameters");
        }
        
        // Return the optimal dimensions
        return {
            width: Math.round(width),
            height: Math.round(height),
            velocity: velocity,
            pressureDrop: pressureDrop
        };
    }
}
