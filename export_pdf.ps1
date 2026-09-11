$ppt = New-Object -ComObject PowerPoint.Application
$optReadOnly = [Microsoft.Office.Core.MsoTriState]::msoTrue
$optUntitled = [Microsoft.Office.Core.MsoTriState]::msoFalse
$optWithWindow = [Microsoft.Office.Core.MsoTriState]::msoFalse

$pptxPath = "C:\Users\willi\Downloads\ATS_Sistema_Reclutamiento_IA.pptx"
$pdfPath = "C:\Users\willi\Downloads\ats\assets\deck.pdf"

$pres = $ppt.Presentations.Open($pptxPath, $optReadOnly, $optUntitled, $optWithWindow)
# 32 = ppSaveAsPDF
$pres.SaveAs($pdfPath, 32)
$pres.Close()
$ppt.Quit()

Write-Host "Exported to PDF successfully!"
