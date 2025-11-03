#!/bin/bash
# QuickSight Dashboard Setup Script
# Run this script to set up your SLA Guard dashboard

echo "🚀 Setting up SLA Guard QuickSight Dashboard..."
echo "Account: 508955320780"
echo ""

# Open QuickSight
echo "📊 Opening QuickSight..."
open "https://us-east-1.quicksight.aws.amazon.com/sn/start/data-sets"

echo ""
echo "✅ SETUP INSTRUCTIONS:"
echo "1. Click 'New dataset' in QuickSight"
echo "2. Choose 'S3' as data source"
echo "3. Data source name: 'SLA Guard Data'"
echo "4. Upload manifest file:"
echo "   Bucket: service-efficiency-data-lake-508955320780"
echo "   Key: quicksight-ready/manifest.json"
echo "5. Click 'Connect' → 'Visualize'"
echo ""
echo "🎨 SUGGESTED VISUALIZATIONS:"
echo "• KPI: SLA Compliance (% of HEALTHY tickets)"
echo "• Donut Chart: Risk Level distribution"
echo "• Table: High-risk tickets queue"
echo "• Bar Chart: Tickets by category"
echo ""
echo "🎉 Your Innovation-Brigade dashboard will be ready!"
