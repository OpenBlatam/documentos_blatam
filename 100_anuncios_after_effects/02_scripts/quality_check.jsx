// Quality Check Script
// Valida la calidad de todos los anuncios antes de exportar
// Uso: File > Scripts > Run Script File

(function() {
    app.beginUndoGroup("Quality Check");
    
    var comps = app.project.items;
    var issues = [];
    var checked = 0;
    var passed = 0;
    
    for (var i = 0; i < comps.length; i++) {
        if (comps[i] instanceof CompItem && comps[i].name.indexOf("Comp_") === 0) {
            var comp = comps[i];
            checked++;
            var compIssues = [];
            
            // Verificar resolución
            if (comp.width !== 1080 || comp.height !== 1920) {
                compIssues.push("Resolución incorrecta: " + comp.width + "x" + comp.height);
            }
            
            // Verificar frame rate
            if (comp.frameDuration !== 1/30) {
                compIssues.push("Frame rate incorrecto: " + (1/comp.frameDuration) + "fps");
            }
            
            // Verificar duración
            if (comp.duration !== 15) {
                compIssues.push("Duración incorrecta: " + comp.duration + "s");
            }
            
            // Verificar que tiene CTA
            var hasCTA = false;
            var hasText = false;
            var hasBackground = false;
            
            for (var j = 1; j <= comp.layers.length; j++) {
                var layer = comp.layers[j];
                
                if (layer.name.indexOf("CTA") !== -1 || layer.name.indexOf("cta") !== -1) {
                    hasCTA = true;
                }
                
                if (layer instanceof TextLayer) {
                    hasText = true;
                }
                
                if (layer.name === "Background") {
                    hasBackground = true;
                }
            }
            
            if (!hasCTA) {
                compIssues.push("No tiene CTA visible");
            }
            
            if (!hasText) {
                compIssues.push("No tiene texto");
            }
            
            if (!hasBackground) {
                compIssues.push("No tiene background");
            }
            
            // Verificar safe zones (texto no debe estar en los primeros/last 150px)
            for (var j = 1; j <= comp.layers.length; j++) {
                var layer = comp.layers[j];
                if (layer instanceof TextLayer) {
                    var pos = layer.property("Position").value;
                    if (pos[1] < 150 || pos[1] > comp.height - 150) {
                        compIssues.push("Texto fuera de safe zone: " + layer.name);
                    }
                }
            }
            
            if (compIssues.length === 0) {
                passed++;
            } else {
                issues.push({
                    comp: comp.name,
                    issues: compIssues
                });
            }
        }
    }
    
    // Generar reporte
    var report = "📊 REPORTE DE CALIDAD\n\n";
    report += "Composiciones verificadas: " + checked + "\n";
    report += "✅ Pasaron: " + passed + "\n";
    report += "⚠️ Con problemas: " + issues.length + "\n\n";
    
    if (issues.length > 0) {
        report += "PROBLEMAS ENCONTRADOS:\n\n";
        for (var i = 0; i < issues.length; i++) {
            report += "📁 " + issues[i].comp + ":\n";
            for (var j = 0; j < issues[i].issues.length; j++) {
                report += "  • " + issues[i].issues[j] + "\n";
            }
            report += "\n";
        }
    } else {
        report += "✅ ¡Todas las composiciones pasaron la validación!";
    }
    
    alert(report);
    
    // Guardar reporte en archivo
    var reportFile = new File("/Users/adan/Documents/documentos_blatam/100_anuncios_after_effects/06_documentacion/quality_report.txt");
    reportFile.open("w");
    reportFile.write(report);
    reportFile.close();
    
    app.endUndoGroup();
})();




