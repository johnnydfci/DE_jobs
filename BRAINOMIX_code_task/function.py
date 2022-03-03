import SimpleITK as sitk
from skimage import measure

def lungmask(vol_sitk, t_value, seed_list):
    
   
    size = sitk.Image(vol_sitk).GetSize()
    spacing = sitk.Image(vol_sitk).GetSpacing()
    volarray = sitk.GetArrayFromImage(vol_sitk)

    # binarize the array by the threshold value (t_value)
    volarray[volarray>= t_value]=1
    volarray[volarray<= t_value]=0
    threshold = sitk.GetImageFromArray(volarray)
    threshold.SetSpacing(spacing)

    # fill in the air region by the seed filling algorithm 
    ConnectedThresholdImageFilter = sitk.ConnectedThresholdImageFilter()
    ConnectedThresholdImageFilter.SetLower(0)
    ConnectedThresholdImageFilter.SetUpper(0)
    ConnectedThresholdImageFilter.SetSeedList(seed_list)
#     ConnectedThresholdImageFilter.SetSeedList([(0,0,0),(size[0]-1,size[1]-1,0)]) # for the rest; vol_05(-800)
#     ConnectedThresholdImageFilter.SetSeedList([(0,0,0),(size[0]-1,size[1]-1,0),(487,424,0)]) # for vol_07 (-300)
#     ConnectedThresholdImageFilter.SetSeedList([(0,0,0),(483,474,16),(size[0]-1,size[1]-1,0)]) # for vol_06 (-600)

    #flip the value to get the bodymask 
    bodymask = ConnectedThresholdImageFilter.Execute(threshold)
    bodymask = sitk.ShiftScale(bodymask,-1,-1)
    
    #lung mask =   bodymask -  trehsold
    temp = sitk.GetImageFromArray(sitk.GetArrayFromImage(bodymask)-sitk.GetArrayFromImage(threshold))
    temp.SetSpacing(spacing)
    
    # get rid of the little region inside the lung    
    bm = sitk.BinaryMorphologicalClosingImageFilter()
    bm.SetKernelType(sitk.sitkBall)
    bm.SetKernelRadius(2)
    bm.SetForegroundValue(1)
    lungmask = bm.Execute(temp)
    
    #get the connected region 
    lungmaskarray = sitk.GetArrayFromImage(lungmask)
    label = measure.label(lungmaskarray,connectivity=2)
    props = measure.regionprops(label)

    # find out the regions which are greater than the 0.55 * max area of the connected region
    numPix = []
    for ia in range(len(props)):
        numPix += [props[ia].area]

    maxnum = max(numPix)
#     print(sorted(numPix,reverse=True)[:10])
    for i in range(len(numPix)):        
        if numPix[i]<= 0.55 * maxnum:
            label[label==i+1]=0
        else:
            label[label==i+1]=1
            
    return label


# write the sitk object into a file, following the spacing, region, direction of a template sitk object.
def write_sitk_from_array_by_template(array, template_sitk,sitk_output_path):    
    output_spacing = template_sitk.GetSpacing()
    output_direction = template_sitk.GetDirection()
    output_origin = template_sitk.GetOrigin()

    sitk_output = sitk.GetImageFromArray(array)
    sitk_output.SetSpacing(output_spacing)
    sitk_output.SetDirection(output_direction)
    sitk_output.SetOrigin(output_origin)

    nrrdWriter = sitk.ImageFileWriter()
    nrrdWriter.SetFileName(sitk_output_path)
    nrrdWriter.SetUseCompression(True)
    nrrdWriter.Execute(sitk_output)
#     print()