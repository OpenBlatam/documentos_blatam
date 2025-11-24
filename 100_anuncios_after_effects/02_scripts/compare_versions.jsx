// Compare Versions Script
// Compara dos versiones del proyecto para detectar cambios
// Uso: File > Scripts > Run Script File

(function() {
    app.beginUndoGroup("Compare Versions");
    
    var currentComps = [];
    var comps = app.project.items;
    
    for (var i = 0; i < comps.length; i++) {
        if (comps[i] instanceof CompItem && comps[i].name.indexOf("Comp_") === 0) {
            var comp = comps[i];
            var info = {
                name: comp.name,
                layers: comp.layers.length,
                duration: comp.duration,
                frameRate: 1 / comp.frameDuration
            };
            currentComps.push(info);
        }
    }
    
    var report = "📊 ESTADO ACTUAL DEL PROYECTO\n\n";
    report += "Composiciones: " + currentComps.length + "\n";
    report += "Promedio de capas: " + Math.round(currentComps.reduce(function(a, b) { return a + b.layers; }, 0) / currentComps.length) + "\n";
    report += "Duración promedio: " + (currentComps.reduce(function(a, b) { return a + b.duration; }, 0) / currentComps.length).toFixed(2) + "s\n";
    
    alert(report);
    
    app.endUndoGroup();
})();



