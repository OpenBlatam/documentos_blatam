// Master Workflow Script
// Ejecuta el workflow completo automáticamente
// Uso: File > Scripts > Run Script File

(function() {
    app.beginUndoGroup("Master Workflow");
    
    var steps = [
        { name: "Crear composiciones", script: "bulk_create_ads.jsx" },
        { name: "Aplicar variaciones", script: "apply_variations.jsx" },
        { name: "Aplicar CTAs", script: "apply_cta_templates.jsx" },
        { name: "Aplicar animaciones", script: "advanced_animations.jsx" },
        { name: "Optimizar CTAs", script: "auto_optimize_cta.jsx" },
        { name: "Aplicar paletas", script: "smart_color_palette.jsx" },
        { name: "Categorizar", script: "tag_and_categorize.jsx" },
        { name: "Validar calidad", script: "quality_check.jsx" }
    ];
    
    var proceed = confirm(
        "Workflow completo:\n\n" +
        steps.map(function(s, i) { return (i+1) + ". " + s.name; }).join("\n") +
        "\n\n¿Ejecutar todos los pasos automáticamente?"
    );
    
    if (!proceed) {
        alert("Workflow cancelado.");
        return;
    }
    
    var results = [];
    var scriptsFolder = new File($.fileName).parent;
    
    for (var i = 0; i < steps.length; i++) {
        var step = steps[i];
        var scriptFile = new File(scriptsFolder.fsName + "/" + step.script);
        
        if (scriptFile.exists) {
            try {
                $.evalFile(scriptFile);
                results.push("✅ " + step.name);
            } catch (e) {
                results.push("❌ " + step.name + " (Error: " + e.toString() + ")");
            }
        } else {
            results.push("⚠️ " + step.name + " (Script no encontrado)");
        }
    }
    
    var report = "Workflow completado:\n\n" + results.join("\n");
    alert(report);
    
    app.endUndoGroup();
})();



