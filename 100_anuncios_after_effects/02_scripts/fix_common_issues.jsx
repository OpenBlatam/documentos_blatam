// Fix Common Issues Script
// Corrige problemas comunes automáticamente
// Uso: File > Scripts > Run Script File

(function() {
    app.beginUndoGroup("Fix Common Issues");
    
    var comps = app.project.items;
    var fixed = 0;
    var issues = {
        missingCTA: 0,
        wrongResolution: 0,
        wrongFrameRate: 0,
        textTooSmall: 0,
        outOfSafeZone: 0
    };
    
    for (var i = 0; i < comps.length; i++) {
        if (comps[i] instanceof CompItem && comps[i].name.indexOf("Comp_") === 0) {
            var comp = comps[i];
            var compFixed = false;
            
            // Verificar y corregir resolución
            if (comp.width !== 1080 || comp.height !== 1920) {
                // No se puede cambiar resolución de comp existente, solo reportar
                issues.wrongResolution++;
            }
            
            // Verificar frame rate
            if (Math.abs(comp.frameDuration - 1/30) > 0.001) {
                issues.wrongFrameRate++;
            }
            
            // Verificar CTA
            var hasCTA = false;
            for (var j = 1; j <= comp.layers.length; j++) {
                var layer = comp.layers[j];
                if (layer.name.indexOf("CTA") !== -1) {
                    hasCTA = true;
                    break;
                }
            }
            
            if (!hasCTA) {
                // Crear CTA básico
                var ctaText = comp.layers.addText("Inscríbete hoy");
                ctaText.name = "CTA_Text";
                ctaText.property("Position").setValue([comp.width/2, comp.height - 200]);
                ctaText.property("Opacity").setValueAtTime(12, 100);
                issues.missingCTA++;
                compFixed = true;
            }
            
            // Verificar textos pequeños
            for (var j = 1; j <= comp.layers.length; j++) {
                var layer = comp.layers[j];
                if (layer instanceof TextLayer) {
                    var textProp = layer.property("Source Text");
                    if (textProp) {
                        var textDoc = textProp.value;
                        if (textDoc && textDoc.fontSize < 48) {
                            textDoc.fontSize = 48;
                            textProp.setValue(textDoc);
                            issues.textTooSmall++;
                            compFixed = true;
                        }
                    }
                }
            }
            
            if (compFixed) fixed++;
        }
    }
    
    var report = "✅ CORRECCIONES APLICADAS\n\n";
    report += "Composiciones corregidas: " + fixed + "\n\n";
    report += "Problemas encontrados:\n";
    report += "• CTAs faltantes: " + issues.missingCTA + "\n";
    report += "• Resolución incorrecta: " + issues.wrongResolution + "\n";
    report += "• Frame rate incorrecto: " + issues.wrongFrameRate + "\n";
    report += "• Textos pequeños: " + issues.textTooSmall + "\n";
    
    alert(report);
    
    app.endUndoGroup();
})();



