// Generate Executive Summary Script
// Genera resumen ejecutivo del proyecto completo
// Uso: File > Scripts > Run Script File

(function() {
    app.beginUndoGroup("Generate Executive Summary");
    
    var comps = app.project.items;
    var summary = {
        total: 0,
        categories: {},
        completeness: {
            withCTA: 0,
            withMusic: 0,
            withLogo: 0,
            withText: 0
        },
        avgDuration: 0,
        avgLayers: 0
    };
    
    var durations = [];
    var layerCounts = [];
    
    for (var i = 0; i < comps.length; i++) {
        if (comps[i] instanceof CompItem && comps[i].name.indexOf("Comp_") === 0) {
            summary.total++;
            var comp = comps[i];
            
            durations.push(comp.duration);
            layerCounts.push(comp.layers.length);
            
            var category = "General";
            var compName = comp.name.toLowerCase();
            if (compName.indexOf("awareness") !== -1) category = "Awareness";
            else if (compName.indexOf("conversion") !== -1) category = "Conversion";
            else if (compName.indexOf("education") !== -1) category = "Education";
            else if (compName.indexOf("testimonial") !== -1) category = "Social Proof";
            else if (compName.indexOf("retention") !== -1) category = "Retention";
            
            if (!summary.categories[category]) summary.categories[category] = 0;
            summary.categories[category]++;
            
            for (var j = 1; j <= comp.layers.length; j++) {
                var layer = comp.layers[j];
                if (layer.name.indexOf("CTA") !== -1) summary.completeness.withCTA++;
                if (layer.name.indexOf("Music") !== -1) summary.completeness.withMusic++;
                if (layer.name.indexOf("Logo") !== -1) summary.completeness.withLogo++;
                if (layer instanceof TextLayer) summary.completeness.withText++;
            }
        }
    }
    
    summary.avgDuration = durations.length > 0 ? 
        durations.reduce(function(a, b) { return a + b; }, 0) / durations.length : 0;
    summary.avgLayers = layerCounts.length > 0 ?
        layerCounts.reduce(function(a, b) { return a + b; }, 0) / layerCounts.length : 0;
    
    var completeness = (
        (summary.completeness.withCTA / summary.total * 25) +
        (summary.completeness.withMusic / summary.total * 25) +
        (summary.completeness.withLogo / summary.total * 25) +
        (summary.completeness.withText / summary.total * 25)
    ).toFixed(1);
    
    var report = "📊 RESUMEN EJECUTIVO\n\n";
    report += "Total anuncios: " + summary.total + "\n";
    report += "Completitud: " + completeness + "%\n";
    report += "Duración promedio: " + summary.avgDuration.toFixed(2) + "s\n";
    report += "Capas promedio: " + summary.avgLayers.toFixed(1) + "\n\n";
    report += "Distribución por categoría:\n";
    for (var cat in summary.categories) {
        report += "  • " + cat + ": " + summary.categories[cat] + "\n";
    }
    
    var summaryFile = new File("/Users/adan/Documents/documentos_blatam/100_anuncios_after_effects/06_documentacion/executive_summary.txt");
    summaryFile.open("w");
    summaryFile.encoding = "UTF-8";
    summaryFile.write(report);
    summaryFile.close();
    
    alert(report);
    
    app.endUndoGroup();
})();



