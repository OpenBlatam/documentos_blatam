// Validate Naming Script
// Valida convenciones de nombres en todas las composiciones
// Uso: File > Scripts > Run Script File

(function() {
    app.beginUndoGroup("Validate Naming");
    
    var comps = app.project.items;
    var violations = [];
    var checked = 0;
    
    var namingRules = {
        prefix: "Comp_",
        format: /^Comp_\d{3}_/,
        maxLength: 50
    };
    
    for (var i = 0; i < comps.length; i++) {
        if (comps[i] instanceof CompItem && comps[i].name.indexOf("Comp_") === 0) {
            checked++;
            var comp = comps[i];
            var issues = [];
            
            if (!namingRules.format.test(comp.name)) {
                issues.push("Formato incorrecto (debe ser Comp_XXX_)");
            }
            
            if (comp.name.length > namingRules.maxLength) {
                issues.push("Nombre muy largo (" + comp.name.length + " caracteres)");
            }
            
            // Verificar capas
            for (var j = 1; j <= comp.layers.length; j++) {
                var layer = comp.layers[j];
                if (layer.name === "" || layer.name === "Layer") {
                    issues.push("Capa sin nombre: " + j);
                }
            }
            
            if (issues.length > 0) {
                violations.push({
                    comp: comp.name,
                    issues: issues
                });
            }
        }
    }
    
    var report = "✅ VALIDACIÓN DE NOMBRES\n\n";
    report += "Verificadas: " + checked + "\n";
    report += "Sin problemas: " + (checked - violations.length) + "\n";
    report += "Con problemas: " + violations.length + "\n";
    
    if (violations.length > 0) {
        report += "\nProblemas encontrados:\n";
        for (var i = 0; i < Math.min(violations.length, 10); i++) {
            report += "\n" + violations[i].comp + ":\n";
            for (var j = 0; j < violations[i].issues.length; j++) {
                report += "  • " + violations[i].issues[j] + "\n";
            }
        }
    }
    
    alert(report);
    
    app.endUndoGroup();
})();



