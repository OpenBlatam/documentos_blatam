// Tag and Categorize Script
// Añade tags y categorías a los anuncios para mejor organización
// Uso: File > Scripts > Run Script File

(function() {
    app.beginUndoGroup("Tag and Categorize");
    
    var comps = app.project.items;
    var categorized = 0;
    
    // Categorías y tags
    var categories = {
        "awareness": {
            tags: ["conciencia", "branding", "alcance"],
            color: [0.18, 0.53, 0.87, 1] // Azul
        },
        "conversion": {
            tags: ["venta", "cta", "urgencia"],
            color: [1.0, 0.2, 0.2, 1] // Rojo
        },
        "education": {
            tags: ["tutorial", "educativo", "aprendizaje"],
            color: [0.0, 0.8, 0.4, 1] // Verde
        },
        "social_proof": {
            tags: ["testimonial", "caso", "resultados"],
            color: [1.0, 0.84, 0.0, 1] // Dorado
        },
        "retention": {
            tags: ["fidelización", "comunidad", "valor"],
            color: [0.42, 0.36, 0.91, 1] // Púrpura
        }
    };
    
    // Asignar categorías basadas en nombre o contenido
    for (var i = 0; i < comps.length; i++) {
        if (comps[i] instanceof CompItem && comps[i].name.indexOf("Comp_") === 0) {
            var comp = comps[i];
            var compName = comp.name.toLowerCase();
            var category = null;
            
            // Determinar categoría basada en nombre
            if (compName.indexOf("awareness") !== -1 || compName.indexOf("conciencia") !== -1) {
                category = categories.awareness;
            } else if (compName.indexOf("conversion") !== -1 || compName.indexOf("venta") !== -1) {
                category = categories.conversion;
            } else if (compName.indexOf("education") !== -1 || compName.indexOf("tutorial") !== -1) {
                category = categories.education;
            } else if (compName.indexOf("testimonial") !== -1 || compName.indexOf("caso") !== -1) {
                category = categories.social_proof;
            } else if (compName.indexOf("retention") !== -1 || compName.indexOf("fideliz") !== -1) {
                category = categories.retention;
            } else {
                // Categoría por defecto basada en número
                var categoryKeys = Object.keys(categories);
                category = categories[categoryKeys[i % categoryKeys.length]];
            }
            
            // Añadir comentario con tags
            var comment = "Tags: " + category.tags.join(", ") + "\n";
            comment += "Categoría: " + Object.keys(categories).find(key => categories[key] === category);
            
            // Usar marcador para almacenar información
            comp.markerProperty.setValueAtTime(0, new MarkerValue(comment));
            
            // Añadir color de fondo basado en categoría (opcional)
            for (var j = 1; j <= comp.layers.length; j++) {
                var layer = comp.layers[j];
                if (layer.name === "Background") {
                    try {
                        var solid = layer.source;
                        if (solid instanceof FootageItem && solid.mainSource instanceof SolidSource) {
                            // Mantener color original o aplicar color de categoría
                            // Descomentar para aplicar colores de categoría:
                            // solid.mainSource.color = category.color;
                        }
                    } catch (e) {
                        // Continuar si hay error
                    }
                }
            }
            
            categorized++;
        }
    }
    
    // Generar reporte de categorización
    var report = "🏷️ CATEGORIZACIÓN COMPLETADA\n\n";
    report += "Anuncios categorizados: " + categorized + "\n\n";
    report += "Categorías disponibles:\n";
    for (var key in categories) {
        report += "  • " + key + ": " + categories[key].tags.join(", ") + "\n";
    }
    report += "\nLos tags están guardados en los marcadores de cada composición.";
    
    alert(report);
    
    app.endUndoGroup();
})();




